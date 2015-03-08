def nondet (fn):
    def replacement (*args):
        c = []
        def Return (x):
            c.append(x)
            raise StopIteration()
        nondet_pump(lambda:fn(Return, *args))
        return c

    replacement.__name__ = fn.__name__ + "_unyield"
    return replacement


def nondet_pump (initiator, prefix=[]):
    it = initiator()
    xs = it.next()
    try:
        for p in prefix:
            xs = it.send(p)
        for x in xs:
            nondet_pump(initiator, prefix+[x])
    except StopIteration:
        pass



@nondet
def pythag (Return, amax, bmax,cmax):
    a = yield range(1, amax+1)
    b = yield range(a, bmax+1)
    c = yield range(b, cmax+1)
    if a*a + b*b == c*c:
        Return((a,b,c))


@nondet
def find_sum(Return, num):
  a = yield range(1, 40)
  b = yield range(1, 40)
  if a + b == num:
    Return((a, b))


@nondet
def two_nums(Return):
  a = yield range(1, 10)
  b = yield range(1, 10)
  Return((a, b))


@nondet
def parlor(Return, num):
  a, b = yield two_nums()
  if a + b == num:
    Return((a, b))
