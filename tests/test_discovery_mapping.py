import asyncio
from custom_components.bticino_myhome.gateway import async_discover_gateways
import custom_components.bticino_myhome.gateway as gateway_module

class FakeGateway: 
    pass

def test_discovery_mapping(monkeypatch):
    async def fake_find():
        return [{"address":"192.168.1.10","port":20000,"serialNumber":"ABC","modelName":"MH201","manufacturer":"BTicino S.p.A."}]
    monkeypatch.setattr(gateway_module, "find_gateways", fake_find)
    result=asyncio.run(async_discover_gateways())
    assert result == [{"host":"192.168.1.10","port":20000,"serial":"ABC","model":"MH201","manufacturer":"BTicino S.p.A."}]
