import sys
sys.path.insert(0, "..")
import os
# os.environ['PYOPCUA_NO_TYPO_CHECK'] = 'True'

import asyncio
import logging

from asyncua import Client, Node, ua

from pyzabbix import ZabbixMetric, ZabbixSender

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')


class SubscriptionHandler:
    """
    The SubscriptionHandler is used to handle the data that is received for the subscription.
    """
    async def datachange_notification(self, node: Node, val, data):
        """
        Callback for asyncua Subscription.
        This method will be called when the Client received a data change message from the Server.
        """
        _logger.info('datachange_notification %r %s', node, val)
        # Get the browse_name in order to set the item name for zabbix
        browse_name = await node.read_browse_name()
        result = ZabbixSender(use_config=True).send([ZabbixMetric('pi1111', f"dht22.{browse_name.Name}", val)])
        _logger.info('zabbix send dht22.%s %r', browse_name.Name, result)


async def main():
    """
    Main task of this Client-Subscription example.
    """
    client = Client(url='opc.tcp://localhost:4840/freeopcua/server/')
    async with client:
        idx = await client.get_namespace_index(uri="github.com/awojnarek/opcua-pi")
        humvar = await client.nodes.objects.get_child([f"{idx}:SensorObj", f"{idx}:HumidityValue"])
        tempvar = await client.nodes.objects.get_child([f"{idx}:SensorObj", f"{idx}:TemperatureValue"])
        handler = SubscriptionHandler()
        # We create a Client Subscription.
        subscription = await client.create_subscription(100, handler)
        nodes = [
            humvar,
            tempvar,
        ]
        # We subscribe to data changes for the nodes (variables).
        await subscription.subscribe_data_change(nodes)
        # Keep the thing running.
        while True:
            await asyncio.sleep(10)
        # We delete the subscription (this un-subscribes from the data changes of the two variables).
        # This is optional since closing the connection will also delete all subscriptions.
        await subscription.delete()
        # After one second we exit the Client context manager - this will close the connection.
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
