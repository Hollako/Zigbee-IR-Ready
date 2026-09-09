// Zigbee IR Ready host adapter, LGPL-2.1-or-later. See NOTICE.
#include <algorithm>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <vector>
#include <nlohmann/json.hpp>
#include "IRac.h"
#include "IRrecv.h"
#include "IRsend.h"
#include "IRsend_test.h"
#include "IRutils.h"
#include "send_names.h"
using json = nlohmann::json;
struct Pulse { bool mark; uint32_t duration; uint32_t frequency; uint8_t duty; };
std::vector<Pulse> pulses;
void bridge_record(bool mark, uint32_t duration, uint32_t frequency, uint8_t duty) {
  if (!duration) return;
  if (pulses.size() >= 20000 || duration > 10000000) throw std::runtime_error("Signal too long");
  if (!pulses.empty() && pulses.back().mark == mark && pulses.back().frequency == frequency)
    pulses.back().duration += duration;
  else pulses.push_back({mark, duration, frequency, duty});
}
std::string string_value(const json &j, const char *key, const std::string &fallback) {
  return j.contains(key) ? j.at(key).get<std::string>() : fallback;
}
stdAc::state_t ac_state(const json &j) {
  stdAc::state_t state;
  std::string name = string_value(j, "Protocol", string_value(j,"Vendor","UNKNOWN"));
  state.protocol = strToDecodeType(name.c_str());
  if (!IRac::isProtocolSupported(state.protocol)) throw std::runtime_error("Unsupported HVAC protocol");
  state.model = j.value("Model", -1);
  state.power = j.value("Power", true);
  state.degrees = j.value("Temp", 24.0);
  if (!std::isfinite(state.degrees) || state.degrees < 0 || state.degrees > 50) throw std::runtime_error("Temperature outside 0..50");
  state.celsius = j.value("Celsius", true);
  state.mode = IRac::strToOpmode(string_value(j,"Mode","Auto").c_str());
  state.fanspeed = IRac::strToFanspeed(string_value(j,"FanSpeed","Auto").c_str());
  state.swingv = IRac::strToSwingV(string_value(j,"SwingV","Off").c_str());
  state.swingh = IRac::strToSwingH(string_value(j,"SwingH","Off").c_str());
  state.quiet=j.value("Quiet",false); state.turbo=j.value("Turbo",false);
  state.econo=j.value("Econo",false); state.light=j.value("Light",false);
  state.filter=j.value("Filter",false); state.clean=j.value("Clean",false);
  state.beep=j.value("Beep",false); state.iFeel=j.value("iFeel",false);
  state.sleep=j.value("Sleep",-1); state.clock=j.value("Clock",-1);
  state.sensorTemperature=j.value("SensorTemp",kNoTempValue);
  return state;
}
json run(const json &j) {
  std::string op=j.value("op", "");
  if(op=="catalogue") {
    json climate=json::array(), send=json::array();
    for(int i=1; i<=kLastDecodeType; i++) {
      auto type=static_cast<decode_type_t>(i);
      if(IRac::isProtocolSupported(type)) climate.push_back(typeToString(type));
    }
    for(auto name: send_names) {
      auto type=strToDecodeType(name);
      send.push_back({{"name",name},{"bits",IRsend::defaultBits(type)},{"state",hasACState(type)}});
    }
    return {{"climate",climate},{"send",send},{"api",1}};
  }
  if(op=="decode") {
    const auto timings=j.at("timings").get<std::vector<uint32_t>>();
    if(timings.empty() || timings.size()>4096) throw std::runtime_error("Expected 1..4096 timings");
    IRsendTest capture(0);
    capture.capture.decode_type=UNKNOWN;
    capture.capture.bits=0;
    capture.capture.rawbuf=capture.rawbuf;
    capture.capture.rawlen=timings.size()+1;
    capture.capture.overflow=false;
    capture.capture.repeat=false;
    capture.capture.value=0;
    capture.capture.address=0;
    capture.capture.command=0;
    capture.rawbuf[0]=0;
    for(size_t i=0;i<timings.size();i++) {
      if(!timings[i] || timings[i]>65535) throw std::runtime_error("Invalid timing");
      capture.rawbuf[i+1]=std::max<uint32_t>(1,timings[i]/kRawTick);
    }
    IRrecv receiver(0, timings.size()+2);
    const bool decoded=receiver.decode(&capture.capture);
    if(!decoded || capture.capture.decode_type==UNKNOWN)
      return {{"recognized",false}};
    return {
      {"recognized",true},
      {"protocol",typeToString(capture.capture.decode_type).c_str()},
      {"bits",capture.capture.bits},
      {"data",resultToHexidecimal(&capture.capture).c_str()},
      {"address",capture.capture.address},
      {"command",capture.capture.command},
      {"repeat",capture.capture.repeat}
    };
  }
  pulses.clear();
  if(op=="hvac") {
    IRac ac(0);
    auto state=ac_state(j.at("state"));
    stdAc::state_t prev;
    bool has_prev=j.contains("previous") && !j.at("previous").is_null();
    if(has_prev) prev=ac_state(j.at("previous"));
    if(!ac.sendAc(state,has_prev?&prev:nullptr)) throw std::runtime_error("HVAC encoding failed");
  } else if(op=="send") {
    const auto &command=j.at("command");
    auto name=command.at("Protocol").get<std::string>();
    auto type=strToDecodeType(name.c_str());
    if(type==UNKNOWN || type==UNUSED) throw std::runtime_error("Unsupported send protocol");
    int bits=command.value("Bits",int(IRsend::defaultBits(type)));
    int repeat=command.value("Repeat",0);
    if(bits<1 || bits>4096 || repeat<0 || repeat>10) throw std::runtime_error("Invalid Bits or Repeat");
    IRsend sender(0);
    std::string data=command.at("Data").get<std::string>();
    if(data.rfind("0x",0)==0 || data.rfind("0X",0)==0) data=data.substr(2);
    if(data.empty() || data.find_first_not_of("0123456789abcdefABCDEF")!=std::string::npos) throw std::runtime_error("Data must be a hex string");
    if(hasACState(type)) {
      const size_t nbytes=(bits+7)/8;
      if(data.size()!=nbytes*2) throw std::runtime_error("State Data must contain ceil(Bits/8) bytes");
      // Pad backing storage: upstream senders are designed for caller-owned
      // fixed-size state buffers, including on malformed short input.
      std::vector<uint8_t> bytes(512,0);
      for(size_t i=0;i<data.size();i+=2) bytes[i/2]=std::stoul(data.substr(i,2),nullptr,16);
      for(int i=0;i<=repeat;i++) if(!sender.send(type,bytes.data(),nbytes)) throw std::runtime_error("State send unsupported");
    } else {
      if(bits>64 || data.size()>16) throw std::runtime_error("Scalar Data exceeds 64 bits");
      uint64_t value=std::stoull(data,nullptr,16);
      if(bits<64 && (value>>bits)) throw std::runtime_error("Data does not fit Bits");
      if(!sender.send(type,value,bits,repeat)) throw std::runtime_error("Scalar send unsupported");
    }
  } else throw std::runtime_error("Unknown operation");
  if(pulses.empty()) throw std::runtime_error("Engine produced no signal");
  json output=json::array();
  for(auto p:pulses) output.push_back({p.mark?int64_t(p.duration):-int64_t(p.duration),p.frequency,p.duty});
  return {{"pulses",output}};
}
int main() {
  try {
    std::string input; char c;
    while(std::cin.get(c) && c!='\n') { if(input.size()>=65536) throw std::runtime_error("Request too large"); input+=c; }
    std::cout << run(json::parse(input)).dump() << std::endl;
    return 0;
  } catch(const std::exception &e) {
    std::cout << json({{"error",e.what()}}).dump() << std::endl;
    return 1;
  }
}
