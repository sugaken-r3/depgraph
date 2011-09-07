#!/usr/bin/python
import rpm
import sys
from optparse import OptionParser
import operator
from dgsub.mylist import flatten,uniq

Feat = {} # Feat[feature] => [ providers ]
File = {} # File[filename] => [ providers ]
Reqs = {} # dictionary of rpm name -> list of rpms it depends on
DepGraph = {}
Options = None
Fmt = ".png"

def lookup(feature):
    return Feat[feature] if (feature in Feat) else File[feature] if (feature in File) else []

def builddep():
    if Options.altdbpath:
            rpm.addMacro('_dbpath', Options.altdbpath)
    ts = rpm.TransactionSet()
    mi = ts.dbMatch()

    if Options.altdbpath:
        rpm.delMacro('_dbpath')

    for h in mi:
        arch = h['arch'] if h['arch'] else '(none)'
        name = h['name']+'.'+arch
        Reqs[name] = h['requires']
        for f in h['provides']:
            if f not in Feat:
                Feat[f] = []
            if name not in Feat[f]:
                Feat[f].append(name)
        for f in h['filenames']:
            if f not in File:
                File[f] = []
            if name not in File[f]:
                File[f].append(name)
    
    if Options.verbose:
        print Feat
        print File

    names = Reqs.keys()
    names.sort()
    for name in names:
        # translate requirements (rpm names/features/filenames) to rpm names
        f = flatten([lookup(y) for y in Reqs[name]])
        Reqs[name] = uniq([x for x in f if x != name])
                                 
        if Options.verbose and (name == 'gpg-pubkey.(none)' or
                               name == 'kernel.x86_64' or
                               name == 'kernel-devel.x86_64'):
            print Reqs[name]

    return Reqs

def dependents(p, grph):
    names = [x for x in grph.keys() if p in grph[x]]
    names.sort()
    return names

def showleaves(grph):
    names = grph.keys()
    names.sort()
    for p in names:
        found = False
        for q in names:
            if p in grph[q]:
                found = True
                break
        if not found:
            print p

def dumpall(grph):
    names = grph.keys()
    names.sort()
    for p in names:
        print("%s -> %s" % (p, grph[p]))

def generatedot(grph):
    names = grph.keys()
    names.sort()
    print "digraph G {"
    for p in names:
        for q in grph[p]:
            print('    "%s" -> "%s";' % (p, q))
    print "}"

def saferecursiveerase(grph, m):
    def SRE1(acc, grph, tgt, ws):
        lst = [q for q in tgt if not dependents(q, grph)]
        if not lst:
            return acc

        for q in lst:
            if Options.withyum:
                print("%syum erase %s" % (ws, q))
            elif Options.withrpm:
                print("%srpm -e %s" % (ws, q))
            elif Options.longoutput:
                print("%s%s can be safely erased" % (ws, q))
            else:
                print ws+q

        deps = uniq(flatten([grph[r] for r in lst]))
        for p in lst:
            grph[p] = []

        if deps:
            SRE1(uniq(acc + lst), grph, deps, ws+' ')
        else:
            return acc + lst

    targets = [ x for x in grph.keys() if x.startswith(m+".")]
    targets.sort()
    removed = uniq([ x for x in targets if not dependents(x, grph)])
    for q in removed:
        if Options.withyum:
            print("yum erase %s" % q)
        elif Options.withrpm:
            print("rpm -e %s" % q)
        elif Options.longoutput:
            print("%s can be safely erased" % q)
        else:
            print q
    if not removed:
        for p in [x for x in targets if grph[x]]:
            print>>sys.stderr, ("error: %s required by %s" % (p, grph[p]))
            print>>sys.stderr, ("%s cannot be safely erased" % p)
        sys.exit(1)
        
    deps = uniq(flatten([grph[x] for x in removed]))
    for p in removed:
        grph[p] = []
    SRE1(removed, grph, deps, ' ')

def showdeps(grph, pkg):
    names = [ x for x in grph.keys() if x.startswith(pkg+".")]
    names.sort()
    for p in names:
        if Options.longoutput:
            print("%s depends on %s" % (p, grph[p] if grph[p] else "nothing"))
        else:
            print p + ":"
            for q in grph[p]:
                print "\t%s" % q

def showdependents(grph, pkg):
    names = [x for x in grph.keys() if x.startswith(pkg+".")]
    names.sort()
    for p in names:
        d = dependents(p, grph)
        if Options.longoutput:
            print("%s is depended by %s" % (p, d if d else "nothing"))
        else:
            print p + ":"
            for q in d:
                print "\t%s" % q
            
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-a", "--dump-all", action="store_true", dest="dumpall",
                      default=False, help="dump all dependency data")
    parser.add_option("-d", "--show-deps", action="store", dest="showdeps",
                      metavar="PACKAGE", default=None,
                      help="show dependencies of PACKAGE")
    parser.add_option("-D", "--show-dependent", action="store",
                      dest="dependents", metavar="PACKAGE", default=None,
                      help="show all packages dependent to PACKAGE")
    parser.add_option("-e", "--safe-erasables", action="store",
                      metavar="TARGET", type="string", dest="target",
                      default=None,
                      help="list RPMs that can be safely erased when TARGET is erased")
    parser.add_option("-r", "--rpm", action="store_true", dest="withrpm",
                      default=False,
                      help="generate shell script to erase safely erasable RPMs with rpm command (requires -e; ignored w/o -e)")
    parser.add_option("-y", "--yum", action="store_true", dest="withyum",
                      default=False,
                      help="generate shell script to erase safely erasable RPMs with yum command (requires -e; ignored w/o -e)")
    parser.add_option("-p", "--dbpath", dest="altdbpath", metavar="PATH",
                      action="store", type="string", default=None,
                      help="set alternative db path to PATH")
    parser.add_option("-s", "--show-leaves", action="store_true",
                      dest="showleaves", default=False,
                      help="show all leaves; i.e. RPMs with no dependent")
    parser.add_option("-t", "--terse", dest="longoutput", action="store_false",
                      default=True,
                      help="turn off human-readable output when listing RPMs")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                      default=False, help="print verbose messages")
    parser.add_option("-z", "--gen-dot", action="store_true",
                      dest="gendot", default="False",
                      help="generate text output in graphviz dot format")
    (Options, args) = parser.parse_args()

    DepGraph = builddep()
    if Options.dumpall:
        dumpall(DepGraph)
    elif Options.showdeps:
        showdeps(DepGraph, Options.showdeps)
    elif Options.dependents:
        showdependents(DepGraph, Options.dependents)
    elif Options.showleaves:
        showleaves(DepGraph)
    elif Options.target:
        saferecursiveerase(DepGraph, Options.target)
    elif Options.gendot:
        generatedot(DepGraph)

    sys.exit(0)
