from script.runtime import Runtime



if __name__ == "__main__":

    rt: Runtime = Runtime()
    print(rt)

    print(rt.run("!sum([2, 4, 6])"))
    print(rt)
