#!/usr/bin/python
#-*- coding: UTF-8 -*-

from baidubaike import Page

if __name__ == "__main__":
    for word in [ 'google', u'异界之暗黑召唤师', u'不存在的帖子']:
        print u"\n====================\nPage: %s" % word
        p = Page(word)
        print "\nInfo:"
        print "\n".join( '%s:\t%s' % (k,v) for k,v in p.get_info().items() )
        print "\nSummary:"
        print p.get_summary()
        print "\nTags:"
        print ", ".join( p.get_tags() )

