
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

        if ('main' not in c) or (not isinstance(c['main'], MType)):
            raise NoEntryPoint()
                
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
            param_envir[paramname] = Unknown() if param.varDimen == [] else ArrayType(param.varDimen.copy(), Unknown())
      
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
                type1 = total_envir[paramname]
                type2 = total_envir[ast.name.name].intype[paramindex]
                if type1 == Unknown():
                    type1 = type2
                    total_envir[paramname] = type2
                if isinstance(type1, ArrayType):
                    if type1.eletype == Unknown():
                        type1.eletype = type2.eletype
                        total_envir[paramname].eletype = type2.eletype
                if type2 == Unknown():
                    type2 = type1
                    total_envir[ast.name.name].intype[paramindex] = type1
                if isinstance(type2, ArrayType):
                    if type2.eletype == Unknown():
                        type2.eletype = type1.eletype
                        total_envir[ast.name.name].intype[paramindex].eletype = type1.eletype

                if type1 != type2: # does this happen ???
                    raise TypeMismatchInStatement(stmt)
        
        # update global environment
        for name in c:
            if name not in local_envir:
                c[name] = total_envir[name]

    def visitAssign(self,ast, c):
        rtype = self.visit(ast.rhs, c)
        ltype = self.visit(ast.lhs, c)
        if ltype == TypeCannotInferred() or rtype == TypeCannotInferred():
            raise TypeCannotBeInferred(ast)

        if ltype == Unknown() and rtype == Unknown():
            raise TypeCannotBeInferred(ast)
        elif ltype == Unknown() and rtype != Unknown():
            if isinstance(rtype, ArrayType):
                raise TypeMismatchInStatement(ast)
            if isinstance(ast.lhs, Id):
                c[ast.lhs.name] = rtype
            elif isinstance(ast.lhs, ArrayCell):
                if isinstance(ast.lhs.arr, Id):
                    c[ast.lhs.arr.name].eletype = rtype
                elif isinstance(ast.lhs.arr, CallExpr):
                    c[ast.lhs.arr.method.name].restype.eletype = rtype
        elif ltype != Unknown() and rtype == Unknown():
            if isinstance(ltype, ArrayType):
                raise TypeMismatchInStatement(ast)
            if isinstance(ast.rhs, Id):
                c[ast.rhs.name] = ltype
            elif isinstance(ast.rhs, ArrayCell):
                if isinstance(ast.rhs.arr, Id):
                    c[ast.rhs.arr.name].eletype = ltype
                elif isinstance(ast.rhs.arr, CallExpr):
                    c[ast.rhs.arr.method.name].restype.eletype = ltype
            elif isinstance(ast.rhs, CallExpr):
                c[ast.rhs.method.name].restype = ltype
        elif ltype != Unknown() and rtype != Unknown():
            if isinstance(ltype, ArrayType) and not isinstance(rtype, ArrayType):
                raise TypeMismatchInStatement(ast)
            elif not isinstance(ltype, ArrayType) and isinstance(rtype, ArrayType):
                raise TypeMismatchInStatement(ast)
            elif isinstance(ltype, ArrayType) and isinstance(rtype, ArrayType):
                if ltype.dimen != rtype.dimen:
                    raise TypeMismatchInStatement(ast)
                if ltype.eletype == Unknown() and rtype.eletype != Unknown():
                    c[ast.lhs.name].eletype = rtype.eletype
                elif ltype.eletype != Unknown() and rtype.eletype == Unknown():
                    if isinstance(ast.rhs, Id):
                        c[ast.rhs.name].eletype = ltype.eletype
                    elif isinstance(ast.rhs, CallExpr):
                        c[ast.rhs.method.name].restype.eletype = ltype.eletype
                elif ltype.eletype == Unknown() and rtype.eletype == Unknown():
                    raise TypeCannotBeInferred(ast)
                elif ltype.eletype != Unknown() and rtype.eletype != Unknown():
                    if ltype.eletype != rtype.eletype:
                        raise TypeMismatchInStatement(ast)
            elif not isinstance(ltype, ArrayType) and not isinstance(rtype, ArrayType):
                if ltype != rtype:
                    raise TypeMismatchInStatement(ast)

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
        if ltype == TypeCannotInferred() or rtype == TypeCannotInferred():
            return TypeCannotInferred() # return message to containing stmt (raise TypeCannotBeInferred at containing stmt)

        typedict = {}
        typedict.update({operator: {'operand_type': IntType(), 'return_type': IntType()} for operator in ['+', '-', '*', '\\', '%']})
        typedict.update({operator: {'operand_type': IntType(), 'return_type': BoolType()} for operator in ['==', '!=', '<', '>', '<=', '>=']})
        typedict.update({operator: {'operand_type': FloatType(), 'return_type': FloatType()} for operator in ['+.', '-.', '*.', '\\.']})
        typedict.update({operator: {'operand_type': FloatType(), 'return_type': BoolType()} for operator in ['=/=', '<.', '>.', '<=.', '>=.']})
        typedict.update({operator: {'operand_type': BoolType(), 'return_type': BoolType()} for operator in ['&&', '||']})

        # lhs type inference
        if ltype == Unknown():  # lhs is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
            ltype = typedict[ast.op]['operand_type']
            if isinstance(ast.left, Id):
                c[ast.left.name] = ltype
            elif isinstance(ast.left, CallExpr):
                c[ast.left.method.name].restype = ltype
            elif isinstance(ast.left, ArrayCell):   # lhs is ArrayCell(Id or func call with dimension)
                if isinstance(ast.left.arr, Id):    # ArrayCell is Id[] (Id type is ArrayType([], eletype?))
                    c[ast.left.arr.name].eletype = ltype
                elif isinstance(ast.left.arr, CallExpr): # ArrayCell is funccall()[] (return type is ArrayType([], eletype?))
                    c[ast.left.arr.method.name].restype.eletype = ltype
        # rhs type inference
        if rtype == Unknown():  # rhs is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
            rtype = typedict[ast.op]['operand_type']
            if isinstance(ast.right, Id):
                c[ast.right.name] = rtype
            elif isinstance(ast.right, CallExpr):
                c[ast.right.method.name].restype = rtype
            elif isinstance(ast.right, ArrayCell):   # rhs is ArrayCell(Id or func call with dimension)
                if isinstance(ast.right.arr, Id):    # ArrayCell is Id[] (Id type is ArrayType([], eletype?))
                    c[ast.right.arr.name].eletype = rtype
                elif isinstance(ast.right.arr, CallExpr): # ArrayCell is funccall()[] (return type is ArrayType([], eletype?))
                    c[ast.right.arr.method.name].restype.eletype = rtype
        # type checking
        if ltype != typedict[ast.op]['operand_type'] or rtype != typedict[ast.op]['operand_type']:
            raise TypeMismatchInExpression(ast)
        return typedict[ast.op]['return_type']



    def visitUnaryOp(self,ast, c):
        exptype = self.visit(ast.body, c)
        if exptype == TypeCannotInferred():
            return TypeCannotInferred() # return message to containing stmt (raise TypeCannotBeInferred at containing stmt)

        typedict = {
            '-': {'operand_type': IntType(), 'return_type': IntType()},
            '-.': {'operand_type': FloatType(), 'return_type': FloatType()},
            '!': {'operand_type': BoolType(), 'return_type': BoolType()}
        }
        # type inference
        if exptype == Unknown():  # body is Id or CallExpr(func call) or ArrayCell(Id or func call with dimension)
            exptype = typedict[ast.op]['operand_type']
            if isinstance(ast.body, Id):
                c[ast.body.name] = exptype
            elif isinstance(ast.body, CallExpr):
                c[ast.body.method.name].restype = exptype
            elif isinstance(ast.body, ArrayCell):   # body is ArrayCell(Id or func call with dimension)
                if isinstance(ast.body.arr, Id):    # ArrayCell is Id[] (Id type is ArrayType([], eletype?))
                    c[ast.body.arr.name].eletype = exptype
                elif isinstance(ast.body.arr, CallExpr): # ArrayCell is funccall()[] (return type is ArrayType([], eletype?))
                    c[ast.body.arr.method.name].restype.eletype = exptype
        # type checking
        if exptype != typedict[ast.op]['operand_type']:
            raise TypeMismatchInExpression(ast)
        return typedict[ast.op]['return_type']
    
                
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
            elif type1 != Unknown() and type2 != Unknown():
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
        arrtype = self.visit(ast.arr, c)
        if arrtype == TypeCannotInferred():
            return TypeCannotInferred() # return message to containing stmt (raise TypeCannotBeInferred at containing stmt)

        if len(arrtype.dimen) != len(ast.idx):
            raise TypeMismatchInExpression(ast)
        for index in ast.idx:
            indextype = self.visit(index, c)
            if isinstance(indextype, ArrayType):
                raise TypeMismatchInExpression(ast)
            if indextype == Unknown():  # index is Id or CallExpr or ArrayCell
                if isinstance(index, Id):
                    c[index.name] = IntType()
                elif isinstance(index, CallExpr):
                    c[index.method.name].restype = IntType()
                elif isinstance(index, ArrayCell):
                    c[index.arr.name].eletype = IntType()
            if indextype != IntType():
                raise TypeMismatchInExpression(ast)
        return self.visit(ast.arr, c)


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
        innertype = Unknown()
        innerdimen = []
        for ele in ast.value:
            inner_ele_type = self.visit(ele, c)
            if innertype != Unknown() and innertype != inner_ele_type:
                raise InvalidArrayLiteral(ast)
            innertype = inner_ele_type
            if isinstance(ele, ArrayLiteral):
                eletype = innertype.eletype
                innerdimen = innertype.dimen
            else:
                eletype = innertype
        dimen += innerdimen
        return ArrayType(dimen, eletype)




        
