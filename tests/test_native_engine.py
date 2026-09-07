"""Executable regression tests; run on Linux after engine/build.py."""
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / 'custom_components/tuya_ir_bridge'
ARCH = {'x86_64':'amd64','aarch64':'aarch64'}.get(platform.machine())
BINARY = COMPONENT / 'bin' / f'ir-engine-{ARCH}'

# Import pure transport modules without importing Home Assistant integration setup.
package = types.ModuleType('ir_transport_test')
package.__path__ = [str(COMPONENT)]
sys.modules[package.__name__] = package
spec = importlib.util.spec_from_file_location('ir_transport_test.signal', COMPONENT/'signal.py')
signal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(signal)


def request(message):
    result = subprocess.run([str(BINARY)], input=json.dumps(message), text=True, capture_output=True, timeout=15)
    data = json.loads(result.stdout)
    if result.returncode:
        raise ValueError(data.get('error'))
    return data


class TransportTests(unittest.TestCase):
    def test_carrier_and_terminal_gap(self):
        result={'pulses':[[2400,40000,33],[-600,40000,33],[1200,40000,33],[-100000,40000,33]]}
        payload,duration=signal.prepare_signal(result)
        self.assertEqual(json.loads(payload)['key1']['freq'],40000)
        self.assertAlmostEqual(duration,.1042)
        with self.assertRaises(ValueError): signal.prepare_signal(result,'base64')

    def test_internal_gap_not_silently_corrupted(self):
        with self.assertRaises(ValueError):
            signal.prepare_signal({'pulses':[[500,38000,50],[-100000,38000,50],[500,38000,50]]})


@unittest.skipUnless(sys.platform=='linux' and BINARY.exists(), 'Bundled Linux engine required')
class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        BINARY.chmod(BINARY.stat().st_mode | 0o100)

    def test_catalogue_covers_requested_families(self):
        catalogue=request({'op':'catalogue'})
        self.assertTrue({'ELECTRA_AC','GREE','MITSUBISHI_AC','DAIKIN'} <= set(catalogue['climate']))
        self.assertTrue({'NEC','SONY','RC5','RC6','SAMSUNG'} <= {p['name'] for p in catalogue['send']})

    def test_ac_families_generate_state_dependent_timings(self):
        for protocol in ('ELECTRA_AC','GREE','MITSUBISHI_AC','DAIKIN','FUJITSU_AC','PANASONIC_AC'):
            with self.subTest(protocol=protocol):
                state={'Protocol':protocol,'Power':True,'Mode':'Cool','Temp':24,'FanSpeed':'Auto'}
                first=request({'op':'hvac','state':state})
                second=request({'op':'hvac','state':{**state,'Temp':25}})
                self.assertNotEqual(first['pulses'],second['pulses'])
                signal.prepare_signal(first)

    def test_electra_matches_python_reference(self):
        spec=importlib.util.spec_from_file_location('reference',COMPONENT/'protocols.py')
        reference=importlib.util.module_from_spec(spec); spec.loader.exec_module(reference)
        result=request({'op':'hvac','state':{'Protocol':'ELECTRA_AC','Power':True,'Mode':'Cool','Temp':24,'FanSpeed':'Auto'}})
        pulses=result['pulses']
        while pulses[-1][0]<0: pulses.pop()
        self.assertEqual([abs(p[0]) for p in pulses],reference.encode_electra('cool',24,'auto'))

    def test_general_send_protocols(self):
        for protocol,bits,data in [('NEC',32,'0x20DF10EF'),('SONY',12,'0xA90'),('RC5',12,'0xC86'),('RC6',20,'0x1000C'),('SAMSUNG',32,'0xE0E040BF')]:
            with self.subTest(protocol=protocol):
                result=request({'op':'send','command':{'Protocol':protocol,'Bits':bits,'Data':data}})
                self.assertTrue(result['pulses'])
                signal.prepare_signal(result)

    def test_non_byte_aligned_state(self):
        result=request({'op':'send','command':{'Protocol':'CARRIER_AC84','Bits':84,'Data':'00'*11}})
        self.assertTrue(result['pulses'])
        signal.prepare_signal(result)

    def test_invalid_requests(self):
        for command in [{'Protocol':'NO_SUCH','Data':'0x1'}, {'Protocol':'NEC','Bits':4,'Data':'0xFFFF'}, {'Protocol':'NEC','Bits':32,'Data':'0x12','Repeat':100}]:
            with self.assertRaises(ValueError): request({'op':'send','command':command})
