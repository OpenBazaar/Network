from twisted.trial import unittest

from dht.routing import KBucket, RoutingTable
from dht.utils import digest
from dht.node import Node
from dht.tests.utils import mknode


class KBucketTest(unittest.TestCase):
    def test_split(self):
        bucket = KBucket(0, 10, 5)
        bucket.addNode(mknode(intid=5))
        bucket.addNode(mknode(intid=6))
        one, two = bucket.split()
        self.assertEqual(len(one), 1)
        self.assertEqual(one.range, (0, 5))
        self.assertEqual(len(two), 1)
        self.assertEqual(two.range, (6, 10))

    def test_addNode(self):
        # when full, return false
        bucket = KBucket(0, 10, 2)
        self.assertTrue(bucket.addNode(mknode()))
        self.assertTrue(bucket.addNode(mknode()))
        self.assertFalse(bucket.addNode(mknode()))
        self.assertEqual(len(bucket), 2)

        # make sure when a node is double added it's put at the end
        bucket = KBucket(0, 10, 3)
        nodes = [mknode(), mknode(), mknode()]
        for node in nodes:
            bucket.addNode(node)
        for index, node in enumerate(bucket.getNodes()):
            self.assertEqual(node, nodes[index])

    def test_removeNode(self):
        bucket = KBucket(0, 10, 2)
        self.assertTrue(bucket.addNode(mknode(intid=1)))
        self.assertTrue(bucket.addNode(mknode(intid=2)))
        bucket.removeNode(mknode(intid=1))
        self.assertEqual(len(bucket), 1)
        bucket.replacementNodes.push(mknode(intid=3))
        bucket.removeNode(mknode(intid=2))
        self.assertEqual(len(bucket), 1)

    def test_inRange(self):
        bucket = KBucket(0, 10, 10)
        self.assertTrue(bucket.hasInRange(mknode(intid=5)))
        self.assertFalse(bucket.hasInRange(mknode(intid=11)))
        self.assertTrue(bucket.hasInRange(mknode(intid=10)))
        self.assertTrue(bucket.hasInRange(mknode(intid=0)))


class RoutingTableTest(unittest.TestCase):
    def setUp(self):
        self.node = Node(digest("test"), "127.0.0.1", 1234)
        self.router = RoutingTable(self, 20, self.node.id)

    def test_addContact(self):
        self.router.addContact(mknode())
        self.assertTrue(len(self.router.buckets), 1)
        self.assertTrue(len(self.router.buckets[0].nodes), 1)

    def test_addDuplicate(self):
        self.router.addContact(self.node)
        self.router.addContact(self.node)
        self.assertTrue(len(self.router.buckets), 1)
        self.assertTrue(len(self.router.buckets[0].nodes), 1)

    def test_addSameIP(self):
        self.router.addContact(self.node)
        self.router.addContact(Node(digest("asdf"), "127.0.0.1", 1234))
        self.assertTrue(len(self.router.buckets), 1)
        self.assertTrue(len(self.router.buckets[0].nodes), 1)
        self.assertTrue(self.router.buckets[0].getNodes()[0].id == digest("asdf"))
