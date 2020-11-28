
"""
 * @author nhphung
"""
from abc import ABC, abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import List, Tuple
from AST import * 
from Visitor import *
from StaticError import *
from functools import *

class Type(ABC):
    __metaclass__ = ABCMeta
    pass
class Prim(Type):
    __metaclass__ = ABCMeta
    pass

@dataclass
class IntType(Prim):
    _type: str = 'int'

@dataclass
class FloatType(Prim):
    _type: str = 'float'

@dataclass
class StringType(Prim):
    _type: str = 'string'

@dataclass
class BoolType(Prim):
    _type: str = 'bool'

@dataclass
class VoidType(Type):
    _type: str = 'void'

@dataclass
class Unknown(Type):
    _type: str = 'unknown'


@dataclass
class ArrayType(Type):
    dimen:List[int]
    eletype: Type

@dataclass
class MType:
    intype:List[Type]
    restype:Type

@dataclass
class TypeCannotInferred:
    value: str = 'type cannnot inferred'

# @dataclass
# class Symbol:
#     name: str
#     mtype:Type

class StaticChecker(BaseVisitor):
    def __init__(self,ast):
        self.ast = ast
        self.global_envi = {
            "int_of_float": MType([FloatType()],IntType()),
            "float_of_int": MType([IntType()],FloatType()),
            "int_of_string": MType([StringType()],IntType()),
            "string_of_int": MType([IntType()],StringType()),
            "float_of_string": MType([StringType()],FloatType()),
            "string_of_float": MType([FloatType()],StringType()),
            "bool_of_string": MType([StringType()],BoolType()),
            "string_of_bool": MType([BoolType()],StringType()),
            "read": MType([],StringType()),
            "printLn": MType([],VoidType()),
            "printStr": MType([StringType()],VoidType()),
            "printStrLn": MType([StringType()],VoidType())
        }                 
   
    def check(self):
        return self.visit(self.ast,self.global_envi)

    def visitProgram(self,ast, c):
        for decl in ast.decl:
            if isinstance(decl, VarDecl):
                self.visit(decl, c)
            else:
                funcname = decl.name.name
                intype_lst = []
                if funcname in c:
                    raise Redeclared(Function(), funcname)
                for param in decl.param:
                    paramtype = Unknown() if param.varDimen == [] else ArrayType(param.varDimen.copy(), Unknown())
                    intype_lst.append(paramtype)
                c[funcname] = MType(intype_lst, Unknown())
                
        for decl in ast.decl:
            if isinstance(decl, FuncDecl):
                self.visit(decl, c)


    def visitVarDecl(self,ast, c):
        idname = ast.variable.name
        if idname in c:
            raise Redeclared(Variable(), idname)
        idtype = Unknown() if not ast.varInit else self.visit(ast.varInit, c)
        if ast.varDimen != []:
            if idtype == Unknown():
                idtype = ArrayType(ast.varDimen.copy(), Unknown())
            else:
                if ast.varDimen != idtype.dimen:
                    raise TypeMismatchInExpression(ast.varInit) # ???
        c[idname] = idtype

    def visitFuncDecl(self,ast, c):
        # visit param
        param_envir = {}
        for param in ast.param:
            paramname = param.variable.name
            if paramname in param_envir:
                raise Redeclared(Parameter(), paramname)

        # update param of this function from outer environment
        for paramname, paramtype in zip(param_envir, c[ast.name.name].intype):
            param_envir[paramname] = paramtype


        # visit local var declare
        local_envir = param_envir.copy()
        for vardecl in ast.body[0]:
            self.visit(vardecl, local_envir)
        
        # visit statement
        total_envir = {**c, **local_envir}
        for stmt in ast.body[1]:
            self.visit(stmt, total_envir)
            # type inference for function parameters
            for paramname, paramindex in zip(param_envir, range(len(param_envir))):
                type1 = param_envir[paramname]
                type2 = total_envir[ast.name.name].intype[paramindex]
                if type1 == Unknown():
                    param_envir[paramname] = type2
                    # update total_envir
                    total_envir.update(param_envir)
                if isinstance(type1, ArrayType):
                    if param_envir[paramname].eletype == Unknown():
                        param_envir[paramname].eletype = type2.eletype
                        # update total_envir
                        total_envir.update(param_envir)
                if type2 == Unknown():
                    total_envir[ast.name.name].intype[paramindex] = type1
                if isinstance(type2, ArrayType):
                    if total_envir[ast.name.name].intype[paramindex].eletype == Unknown():
                        total_envir[ast.name.name].intype[paramindex].eletype = type1.eletype
                if type1 != type2: # does this happen ???
                    raise TypeMismatchInStatement(stmt)
        
        # update global environment
        for name in c:
            if name not in local_envir:
                c[name] = total_envir[name]

    def visitAssign(self,ast, c):
        pass

    def visitIf(self,ast, c):
        pass

    def visitFor(self,ast, c):
        pass

    def visitBreak(self,ast, c):
        pass

    def visitContinue(self,ast, c):
        pass

    def visitReturn(self,ast, c):
        pass

    def visitDowhile(self,ast, c):
        pass

    def visitWhile(self,ast, c):
        pass

    def visitCallStmt(self,ast, c):
        pass

    def visitBinaryOp(self,ast, c):
        ltype = self.visit(ast.left, c)
        rtype = self.visit(ast.right, c)
        if ast.op in ['+', '-', '*', '\\', '\\%', '==', '!=', '<', '>', '<=', '>=']:
            # lhs type inference
            if ltype == Unknown():  # lhs is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
                if isinstance(ast.left, Id):
                    ltype = IntType()
                    c[ast.left.name] = ltype
                elif isinstance(ast.left, CallExpr):
                    ltype = IntType()
                    c[ast.left.method.name].restype = ltype
                elif isinstance(ast.left, ArrayCell):   # lhs is ArrayCell(Id or func call with dimension)
                    if isinstance(ast.left.arr, Id):    # ArrayCell is Id[] (Id type is ArrayType([], eletype?))
                        ltype = IntType()
                        c[ast.left.arr.name].eletype = ltype
                    elif isinstance(ast.left.arr, CallExpr): # ArrayCell is funccall()[] (return type is ArrayType([], eletype?))
                        ltype = IntType()
                        c[ast.left.arr.method.name].restype.eletype = ltype
            # rhs type inference
            if rtype == Unknown():  # rhs is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
                if isinstance(ast.right, Id):
                    rtype = IntType()
                    c[ast.right.name] = rtype
                elif isinstance(ast.right, CallExpr):
                    rtype = IntType()
                    c[ast.right.method.name].restype = rtype
                elif isinstance(ast.right, ArrayCell):   # rhs is ArrayCell(Id or func call with dimension)
                    if isinstance(ast.right.arr, Id):    # ArrayCell is Id[] (Id type is ArrayType([], eletype?))
                        rtype = IntType()
                        c[ast.right.arr.name].eletype = rtype
                    elif isinstance(ast.right.arr, CallExpr): # ArrayCell is funccall()[] (return type is ArrayType([], eletype?))
                        rtype = IntType()
                        c[ast.right.arr.method.name].restype.eletype = rtype
            # type checking
            if ltype != IntType() or rtype != IntType():
                raise TypeMismatchInExpression(ast)
            return IntType() if ast.op in ['+', '-', '*', '\\', '\\%'] else BoolType()
        elif ast.op in ['+.', '-.', '*.', '\\.', '=/=', '<.', '>.', '<=.', '>=.']:
            # lhs type inference
            if ltype == Unknown():  # lhs is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
                if isinstance(ast.left, Id):
                    ltype = FloatType()
                    c[ast.left.name] = ltype
                elif isinstance(ast.left, CallExpr):
                    ltype = FloatType()
                    c[ast.left.method.name].restype = ltype
                elif isinstance(ast.left, ArrayCell):   # lhs is ArrayCell(Id or func call with dimension)
                    if isinstance(ast.left.arr, Id):    # ArrayCell is Id[] (Id type is ArrayType([], eletype?))
                        ltype = FloatType()
                        c[ast.left.arr.name].eletype = ltype
                    elif isinstance(ast.left.arr, CallExpr): # ArrayCell is funccall()[] (return type is ArrayType([], eletype?))
                        ltype = FloatType()
                        c[ast.left.arr.method.name].restype.eletype = ltype
            # rhs type inference
            if rtype == Unknown():  # rhs is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
                if isinstance(ast.right, Id):
                    rtype = FloatType()
                    c[ast.right.name] = rtype
                elif isinstance(ast.right, CallExpr):
                    rtype = FloatType()
                    c[ast.right.method.name].restype = rtype
                elif isinstance(ast.right, ArrayCell):   # rhs is ArrayCell(Id or func call with dimension)
                    if isinstance(ast.right.arr, Id):    # ArrayCell is Id[] (Id type is ArrayType([], eletype?))
                        rtype = FloatType()
                        c[ast.right.arr.name].eletype = rtype
                    elif isinstance(ast.right.arr, CallExpr): # ArrayCell is funccall()[] (return type is ArrayType([], eletype?))
                        rtype = FloatType()
                        c[ast.right.arr.method.name].restype.eletype = rtype
            # type checking
            if ltype != FloatType() or rtype != FloatType():
                raise TypeMismatchInExpression(ast)
            return FloatType() if ast.op in ['+.', '-.', '*.', '\\.'] else BoolType()
        elif ast.op in ['&&', '||']:
            # lhs type inference
            if ltype == Unknown():  # lhs is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
                if isinstance(ast.left, Id):
                    ltype = BoolType()
                    c[ast.left.name] = ltype
                elif isinstance(ast.left, CallExpr):
                    ltype = BoolType()
                    c[ast.left.method.name].restype = ltype
                elif isinstance(ast.left, ArrayCell):   # lhs is ArrayCell(Id or func call with dimension)
                    if isinstance(ast.left.arr, Id):    # ArrayCell is Id[] (Id type is ArrayType([], eletype?))
                        ltype = BoolType()
                        c[ast.left.arr.name].eletype = ltype
                    elif isinstance(ast.left.arr, CallExpr): # ArrayCell is funccall()[] (return type is ArrayType([], eletype?))
                        ltype = BoolType()
                        c[ast.left.arr.method.name].restype.eletype = ltype
            # rhs type inference
            if rtype == Unknown():  # rhs is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
                if isinstance(ast.right, Id):
                    rtype = BoolType()
                    c[ast.right.name] = rtype
                elif isinstance(ast.right, CallExpr):
                    rtype = BoolType()
                    c[ast.right.method.name].restype = rtype
                elif isinstance(ast.right, ArrayCell):   # rhs is ArrayCell(Id or func call with dimension)
                    if isinstance(ast.right.arr, Id):    # ArrayCell is Id[] (Id type is ArrayType([], eletype?))
                        rtype = BoolType()
                        c[ast.right.arr.name].eletype = rtype
                    elif isinstance(ast.right.arr, CallExpr): # ArrayCell is funccall()[] (return type is ArrayType([], eletype?))
                        rtype = BoolType()
                        c[ast.right.arr.method.name].restype.eletype = rtype
            # type checking
            if ltype != BoolType() or rtype != BoolType():
                raise TypeMismatchInExpression(ast)
            return BoolType()
      


    def visitUnaryOp(self,ast, c):
        exptype = self.visit(ast.body, c)
        if ast.op == '-':
            # type inference
            if exptype == Unknown():  # body is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
                if isinstance(ast.body, Id):
                    exptype = IntType()
                    c[ast.body.name] = exptype
                elif isinstance(ast.body, CallExpr):
                    exptype = IntType()
                    c[ast.body.method.name].restype = exptype
                elif isinstance(ast.body, ArrayCell):   # body is ArrayCell(Id or func call with dimension)
                    if isinstance(ast.body.arr, Id):    # ArrayCell is Id[] (Id type is ArrayType([], eletype?))
                        exptype = IntType()
                        c[ast.body.arr.name].eletype = exptype
                    elif isinstance(ast.body.arr, CallExpr): # ArrayCell is funccall()[] (return type is ArrayType([], eletype?))
                        exptype = IntType()
                        c[ast.body.arr.method.name].restype.eletype = exptype
            # type checking
            if exptype != IntType():
                raise TypeMismatchInExpression(ast)
            return IntType()
        elif ast.op == '-.':
            # type inference
            if exptype == Unknown():  # body is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
                if isinstance(ast.body, Id):
                    exptype = FloatType()
                    c[ast.body.name] = exptype
                elif isinstance(ast.body, CallExpr):
                    exptype = FloatType()
                    c[ast.body.method.name].restype = exptype
                elif isinstance(ast.body, ArrayCell):   # body is ArrayCell(Id or func call with dimension)
                    if isinstance(ast.body.arr, Id):    # ArrayCell is Id[] (Id type is ArrayType([], eletype?))
                        exptype = FloatType()
                        c[ast.body.arr.name].eletype = exptype
                    elif isinstance(ast.body.arr, CallExpr): # ArrayCell is funccall()[] (return type is ArrayType([], eletype?))
                        exptype = FloatType()
                        c[ast.body.arr.method.name].restype.eletype = exptype
            # type checking
            if exptype != FloatType():
                raise TypeMismatchInExpression(ast)
            return FloatType()
        elif ast.op == '!':
            # type inference
            if exptype == Unknown():  # body is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
                if isinstance(ast.body, Id):
                    exptype = BoolType()
                    c[ast.body.name] = exptype
                elif isinstance(ast.body, CallExpr):
                    exptype = BoolType()
                    c[ast.body.method.name].restype = exptype
                elif isinstance(ast.body, ArrayCell):   # body is ArrayCell(Id or func call with dimension)
                    if isinstance(ast.body.arr, Id):    # ArrayCell is Id[] (Id type is ArrayType([], eletype?))
                        exptype = BoolType()
                        c[ast.body.arr.name].eletype = exptype
                    elif isinstance(ast.body.arr, CallExpr): # ArrayCell is funccall()[] (return type is ArrayType([], eletype?))
                        exptype = BoolType()
                        c[ast.body.arr.method.name].restype.eletype = exptype
            # type checking
            if exptype != BoolType():
                raise TypeMismatchInExpression(ast)
            return BoolType()
                
    # check intype
    # return restype
    def visitCallExpr(self,ast, c):
        if ast.method.name not in c:
            raise Undeclared(Function(), ast.method.name)
        if not isinstance(c[ast.method.name], MType):
            raise Undeclared(Function(), ast.method.name)
        if len(ast.param) != len(c[ast.method.name].intype):
            raise TypeMismatchInExpression(ast)
        for i in range(len(ast.param)):
            # type inference
            type1 = c[ast.method.name].intype[i]    # param type
            type2 = self.visit(ast.param[i], c)     # argument type
            if type1 == Unknown() and type2 != Unknown():  # param is Id (param cannot be CallExpr)
                if isinstance(type2, ArrayType):
                    raise TypeMismatchInExpression(ast)
                c[ast.method.name].intype[i] = type2
            elif type1 != Unknown() and type2 == Unknown():  # arg is Id or CallExpr
                if isinstance(type1, ArrayType):
                    raise TypeMismatchInExpression(ast)
                if isinstance(ast.param[i], Id):
                    c[ast.param[i].name] = type1
                elif isinstance(ast.param[i], CallExpr):
                    c[ast.param[i].method.name].restype = type1
            elif type1 == Unknown() and type2 == Unknown():
                return TypeCannotInferred() # return message to containing stmt (raise TypeCannotBeInferred at containing stmt)
            elif type1 != Unknown and type2 != Unknown():
                if isinstance(type1, ArrayType) and not isinstance(type2, ArrayType):
                    raise TypeMismatchInExpression(ast)
                elif not isinstance(type1, ArrayType) and isinstance(type2, ArrayType):
                    raise TypeMismatchInExpression(ast)
                elif not isinstance(type1, ArrayType) and not isinstance(type2, ArrayType):
                    if type1 != type2:
                        raise TypeMismatchInExpression(ast)
                elif isinstance(type1, ArrayType) and isinstance(type2, ArrayType):
                    if type1.dimen != type2.dimen:
                        raise TypeMismatchInExpression(ast)
                    if type1.eletype == Unknown() and type2.eletype == Unknown():
                        return TypeCannotInferred() # return message to containing stmt (raise TypeCannotBeInferred at containing stmt)
                    elif type1.eletype == Unknown() and type2.eletype != Unknown(): # type1.eletype is Int/Float/Bool/String Type
                        c[ast.method.name].intype[i].eletype = type2.eletype
                    elif type1.eletype != Unknown() and type2.eletype == Unknown(): # ast.param[i]
                        if isinstance(ast.param[i], Id):
                            c[ast.param[i].name].eletype = type1.eletype
                        elif isinstance(ast.param[i], CallExpr):
                            c[ast.param[i].method.name].restype.eletype = type1.eletype
                    elif type1.eletype != Unknown() and type2.eletype != Unknown():
                        if type1.eletype != type2.eletype:
                            raise TypeMismatchInExpression(ast)

        return c[ast.method.name].restype

    # check Undeclare, check index
    # return innermost eletype
    def visitArrayCell(self,ast, c):
        if isinstance(ast.arr, Id):
            if ast.arr.name not in c:
                raise Undeclared(Identifier(), ast.arr.name)
            if len(ast.idx) != len(c[ast.arr.name].dimen):
                raise TypeMismatchInExpression(ast)

    def visitId(self,ast, c):
        if ast.name not in c:
            raise Undeclared(Identifier(), ast.name)
        return c[ast.name]


    def visitIntLiteral(self,ast, c):
        return IntType()

    def visitFloatLiteral(self,ast, c):
        return FloatType()

    def visitStringLiteral(self,ast, c):
        return StringType()

    def visitBooleanLiteral(self,ast, c):
        return BoolType()

    def visitArrayLiteral(self,ast, c):
        eletype = Unknown()
        dimen = [len(ast.value)]
        innerdimen = []
        for ele in ast.value:
            if eletype != Unknown() and eletype != self.visit(ele, c):
                raise InvalidArrayLiteral(ast)
            eletype = self.visit(ele, c)
            if isinstance(ele, ArrayLiteral):
                innerdimen = self.visit(ele, c).dimen
        dimen += innerdimen
        return ArrayType(dimen, eletype)




        
