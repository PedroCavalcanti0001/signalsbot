import asyncio


def say_boo():
    i = 0
    while True:
        yield None
        print("...boo {0}".format(i))
        i += 1


def say_baa():
    i = 0
    while True:
        yield
        print("...baa {0}".format(i))
        i += 1

loop = asyncio.get_event_loop()
boo_task = loop.create_task(say_boo())
baa_task = loop.create_task(say_baa())
loop.run_forever()
