import asyncio
import copy
import logging
from datetime import datetime
import time
from math import sin
import Adafruit_DHT

from asyncua import ua, uamethod, Server

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4
celsius = 37.5

class SubHandler(object):

    """
    Subscription Handler. To receive events from server for a subscription
    """

    def datachange_notification(self, node, val, data):
        print("Python: New data change event", node, val)

    def event_notification(self, event):
        print("Python: New event", event)


# method to be exposed through server

def func(parent, variant):
    ret = False
    if variant.Value % 2 == 0:
        ret = True
    return [ua.Variant(ret, ua.VariantType.Boolean)]


# method to be exposed through server
# uses a decorator to automatically convert to and from variants

@uamethod
def multiply(parent, x, y):
    print("multiply method call with parameters: ", x, y)
    return x * y


async def main():

    # now setup our server
    server = Server()
    await server.init()
    server.disable_clock()  #for debuging
    #server.set_endpoint("opc.tcp://localhost:4840/freeopcua/server/")
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    server.set_server_name("FreeOpcUa Example Server")
    # set all possible endpoint policies for clients to connect through
    server.set_security_policy([
                ua.SecurityPolicyType.NoSecurity,
                ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
                ua.SecurityPolicyType.Basic256Sha256_Sign])

    # setup our own namespace
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    # create a new node type we can instantiate in our address space
    dev = await server.nodes.base_object_type.add_object_type(idx, "MyDevice")
    await (await dev.add_variable(idx, "sensor1", 1.0)).set_modelling_rule(True)
    await (await dev.add_property(idx, "device_id", "0340")).set_modelling_rule(True)
    ctrl = await dev.add_object(idx, "controller")
    await ctrl.set_modelling_rule(True)
    await (await ctrl.add_property(idx, "state", "Idle")).set_modelling_rule(True)

    # populating our address space

    # First a folder to organise our nodes
    myfolder = await server.nodes.objects.add_folder(idx, "SensorData")

    # instanciate one instance of our device
    mydevice = await server.nodes.objects.add_object(idx, "Device0001", dev)
    mydevice_var = await mydevice.get_child([f"{idx}:controller", f"{idx}:state"])  # get proxy to our device state variable

    # create directly some objects and variables
    myobj = await server.nodes.objects.add_object(idx, "HumidityObj")
    myvar = await myobj.add_variable(idx, "HumidityValue", 0.0)
    myvar2 = await myobj.add_variable(idx, "TemperatureValue", 0.0)
    await myvar.set_writable()    # Set MyVariable to be writable by clients
    await myvar2.set_writable()    # Set MyVariable to be writable by clients

    # creating a default event object
    # The event object automatically will have members for all events properties
    # you probably want to create a custom event type, see other examples
    myevgen = await server.get_event_generator()
    myevgen.event.Severity = 300

    # starting!
    async with server:
        print("Available loggers are: ", logging.Logger.manager.loggerDict.keys())

        while True:
            await asyncio.sleep(0.1)
            await server.write_attribute_value(myvar.nodeid, ua.DataValue(sin(time.time())))
            humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
            fahrenheit = (temperature * 1.8) + 32

            if humidity is not None:
                await server.write_attribute_value(myvar.nodeid, ua.DataValue(humidity))

            if temperature is not None:
                await server.write_attribute_value(myvar2.nodeid, ua.DataValue(fahrenheit))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
