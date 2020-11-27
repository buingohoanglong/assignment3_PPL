
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
                funcname = ast.name.name
                if funcname in c:
                    raise Redeclared(Function(), funcname)
                c[funcname] = MType([Unknown()] * len(decl.param), Unknown())
                
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
                idtype = ArrayType([], Unknown())
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
            param_envir[paramname] = Unknown()

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
                if type2 == Unknown():
                    total_envir[ast.name.name].intype[paramindex] = type1
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
            # type inference
            if ltype == Unknown():  # lhs is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
                if isinstance(ast.left, Id):
                    c[ast.left.name] = IntType()
                elif isinstance(ast.left, CallExpr):
                    c[ast.left.method.name].restype = IntType()
                elif isinstance(ast.left, ArrayCell):   # ???
                    pass
            if rtype == Unknown():  # rhs is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
                if isinstance(ast.right, Id):
                    c[ast.right.name] = IntType()
                elif isinstance(ast.right, CallExpr):
                    c[ast.right.method.name].restype = IntType()
                elif isinstance(ast.right, ArrayCell):   # ???
                    pass
            # type checking
            if ltype != IntType() or rtype != IntType():
                raise TypeMismatchInExpression(ast)
            return IntType() if ast.op in ['+', '-', '*', '\\', '\\%'] else BoolType()
        elif ast.op in ['+.', '-.', '*.', '\\.', '=/=', '<.', '>.', '<=.', '>=.']:
            # type inference
            if ltype == Unknown():  # lhs is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
                if isinstance(ast.left, Id):
                    c[ast.left.name] = FloatType()
                elif isinstance(ast.left, CallExpr):
                    c[ast.left.method.name].restype = FloatType()
                elif isinstance(ast.left, ArrayCell):   # ???
                    pass
            if rtype == Unknown():  # rhs is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
                if isinstance(ast.right, Id):
                    c[ast.right.name] = FloatType()
                elif isinstance(ast.right, CallExpr):
                    c[ast.right.method.name].restype = FloatType()
                elif isinstance(ast.right, ArrayCell):   # ???
                    pass
            # type checking
            if ltype != FloatType() or rtype != FloatType():
                raise TypeMismatchInExpression(ast)
            return FloatType() if ast.op in ['+.', '-.', '*.', '\\.'] else BoolType()
        elif ast.op in ['&&', '||']:
            # type inference
            if ltype == Unknown():  # lhs is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
                if isinstance(ast.left, Id):
                    c[ast.left.name] = BoolType()
                elif isinstance(ast.left, CallExpr):
                    c[ast.left.method.name].restype = BoolType()
                elif isinstance(ast.left, ArrayCell):   # ???
                    pass
            if rtype == Unknown():  # rhs is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
                if isinstance(ast.right, Id):
                    c[ast.right.name] = BoolType()
                elif isinstance(ast.right, CallExpr):
                    c[ast.right.method.name].restype = BoolType()
                elif isinstance(ast.right, ArrayCell):   # ???
                    pass
            # type checking
            if ltype != BoolType() or rtype != BoolType():
                raise TypeMismatchInExpression(ast)
            return BoolType()
      


    def visitUnaryOp(self,ast, c):
        exptype = self.visit(ast.body, c)
        if ast.op == '-':
            # type inference
            if exptype == Unknown():  # exp is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
                if isinstance(ast.body, Id):
                    c[ast.body.name] = IntType()
                elif isinstance(ast.body, CallExpr):
                    c[ast.body.method.name].restype = IntType()
                elif isinstance(ast.body, ArrayCell):   # ???
                    pass
            # type checking
            if exptype != IntType():
                raise TypeMismatchInExpression(ast)
            return IntType()
        elif ast.op == '-.':
            # type inference
            if exptype == Unknown():  # exp is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
                if isinstance(ast.body, Id):
                    c[ast.body.name] = FloatType()
                elif isinstance(ast.body, CallExpr):
                    c[ast.body.method.name].restype = FloatType()
                elif isinstance(ast.body, ArrayCell):   # ???
                    pass
            # type checking
            if exptype != FloatType():
                raise TypeMismatchInExpression(ast)
            return FloatType()
        elif ast.op == '!':
            # type inference
            if exptype == Unknown():  # exp is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
                if isinstance(ast.body, Id):
                    c[ast.body.name] = BoolType()
                elif isinstance(ast.body, CallExpr):
                    c[ast.body.method.name].restype = BoolType()
                elif isinstance(ast.body, ArrayCell):   # ???
                    pass
            # type checking
            if exptype != BoolType():
                raise TypeMismatchInExpression(ast)
            return BoolType()
                

    def visitCallExpr(self,ast, c):
        pass

    def visitArrayCell(self,ast, c):
        pass

    def visitId(self,ast, c):
        if ast.name in c:
            return c[ast.name]
        return Unknown()


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




        
