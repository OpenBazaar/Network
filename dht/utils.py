"""
General catchall for functions that don't make sense as methods.

Copyright (c) 2014 Brian Muller
"""
from __future__ import print_function

import hashlib
import operator
import os, sys
import cStringIO

from twisted.internet import defer
from io import BytesIO
from PIL import Image


def digest(s):
    if not isinstance(s, str):
        s = str(s)
    intermed = hashlib.sha256(s).digest()
    d = hashlib.new('ripemd160', intermed).digest()
    return d


def deferredDict(d):
    """
    Just like a :class:`defer.DeferredList` but instead accepts and returns a :class:`dict`.

    Args:
        d: A :class:`dict` whose values are all :class:`defer.Deferred` objects.

    Returns:
        :class:`defer.DeferredList` whose callback will be given a dictionary whose
        keys are the same as the parameter :obj:`d` and whose values are the results
        of each individual deferred call.
    """
    if len(d) == 0:
        return defer.succeed({})

    def handle(results, names):
        rvalue = {}
        for index in range(len(results)):
            rvalue[names[index]] = results[index][1]
        return rvalue

    dl = defer.DeferredList(d.values())
    return dl.addCallback(handle, d.keys())


class OrderedSet(list):
    """
    Acts like a list in all ways, except in the behavior of the :meth:`push` method.
    """

    def push(self, thing):
        """
        1. If the item exists in the list, it's removed
        2. The item is pushed to the end of the list
        """
        if thing in self:
            self.remove(thing)
        self.append(thing)


def sharedPrefix(args):
    """
    Find the shared prefix between the strings.

    For instance:

        sharedPrefix(['blahblah', 'blahwhat'])

    returns 'blah'.
    """
    i = 0
    while i < min(map(len, args)):
        if len(set(map(operator.itemgetter(i), args))) != 1:
            break
        i += 1
    return args[0][:i]

def resizeImage(image, maxSize):
    """
    Takes an image and a maxSize. For example ("image goes here", (256,256));
    Resizes to a maxSize if the length or width is greater than the maxSize 
    Removes EXIF data
    Converts to .png and returns the image
    """
    image = image[0]
    try:
        openImage = Image.open(cStringIO.StringIO(image))
        if(openImage.size[0]>maxSize[0] or openImage.size[1]>maxSize[1]):
            ratio = min(maxSize[0]/(float(openImage.size[0])), maxSize[1]/(float(openImage.size[1])))
            openImage = openImage.resize((int(openImage.size[0]*ratio),int(openImage.size[1]*ratio)),Image.ANTIALIAS)
            openImage.save("tempCompressedImage.png")
            returnImage= open("tempCompressedImage.png", "rb").read()
            os.remove("tempCompressedImage.png")
            return returnImage
    except Exception:
        pass
return image