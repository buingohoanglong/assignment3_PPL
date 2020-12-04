from dataclasses import dataclass

# class Type():
#     pass

# @dataclass
# class SubType2(Type):
#     _value: str = 'b'

# @dataclass
# class SubType1(Type):
#     _value: str = 'a'
#     _type: SubType2 = SubType2()



# a = SubType1()
# b = SubType1()
# b._value = 'b'
# print(isinstance(b, SubType1))
# print(isinstance(a, SubType1))
# print(isinstance(a, Type))

# a = [[1,2],[3,4],[5,6]]
# def foo(a):
#     return a[0]
# b = foo(a)
# b[0] = 10
# print(b)
# print(a)
# print(foo(a))

@dataclass
class B:
    value: float = 1.1
    _type: str = 'float'

@dataclass
class A:
    value: int = 1
    _type: B = B()



a = {'a':A(), 'b':B()}
del a['a']
print(a)