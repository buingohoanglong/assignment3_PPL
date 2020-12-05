
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
        current_function = {ast.name.name : total_envir[ast.name.name]}
        del total_envir[ast.name.name]
        total_envir = {**total_envir, **current_function}   # append current function to the end of dictionary
        for stmt in ast.body[1]:
            result = self.visit(stmt, total_envir)
            if isinstance(result, Break) or isinstance(result, Continue):
                raise NotInLoop(result)

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

    def visitAssign(self,ast, c):   # left hand side can be in any type except VoidType (what about MType ???)
        ltype = self.visit(ast.lhs, c)
        rtype = self.visit(ast.rhs, c)
        if ltype == TypeCannotInferred() or rtype == TypeCannotInferred():
            raise TypeCannotBeInferred(ast)
        if ltype == VoidType() or rtype == VoidType():
            raise TypeMismatchInStatement(ast)

        # type inference
        ltype, rtype = self.mutual_infer(type1=ltype, type2=rtype, e2=ast.rhs, isStmt=True, isReturnStmt=False, ast=ast)
        # lhs type update
        self.direct_infer(e=ast.lhs, inferred_type=ltype, c=c)
        # rhs type update
        self.direct_infer(e=ast.rhs, inferred_type=rtype, c=c)
        

    def visitIf(self,ast, c):
        result = None   # used to detect not in loop
        current_function_name = list(c.keys())[-1]
        for ifthenstmt in ast.ifthenStmt:
            # visit condition expression
            exptype = self.visit(ifthenstmt[0], c)
            if exptype == TypeCannotInferred():
                raise TypeCannotBeInferred(ast)

            if exptype == Unknown():    # exp is Id, CallExpr, ArrayCell
                exptype = BoolType()
                self.direct_infer(e=ifthenstmt[0], inferred_type=exptype, c=c)
            if exptype != BoolType():
                raise TypeMismatchInStatement(ast)

            # visit if/elif local var declare
            local_envir = {}
            for vardecl in ifthenstmt[1]:
                self.visit(vardecl, local_envir)

            # visit if/elif statement
            total_envir = {**c, **local_envir}
            current_function = {current_function_name : total_envir[current_function_name]}
            del total_envir[current_function_name]
            total_envir = {**total_envir, **current_function}   # append current function to the end of dictionary
            for stmt in ifthenstmt[2]:
                result = self.visit(stmt, total_envir)
    
            # update outer environment
            for name in c:
                if name not in local_envir:
                    c[name] = total_envir[name]
        
        # visit else local var declare
        local_envir = {}
        for vardecl in ast.elseStmt[0]:
            self.visit(vardecl, local_envir)

        # visit else statement
        total_envir = {**c, **local_envir}
        current_function = {current_function_name : total_envir[current_function_name]}
        del total_envir[current_function_name]
        total_envir = {**total_envir, **current_function}   # append current function to the end of dictionary
        for stmt in ast.elseStmt[1]:
            result = self.visit(stmt, total_envir)
        
        # update outer environment
        for name in c:
            if name not in local_envir:
                c[name] = total_envir[name]

        return result
    

    def visitFor(self,ast, c):
        # visit scalar variable
        indextype = self.visit(ast.idx1, c)
        if indextype == Unknown():
            indextype = IntType()
            c[ast.idx1.name] = indextype
        if indextype != Unknown():
            raise TypeMismatchInStatement(ast)

        # visit initExpr (expr1)
        exptype1 = self.visit(ast.expr1, c)
        if exptype1 == TypeCannotInferred():
            raise TypeCannotBeInferred(ast)
        if exptype1 == Unknown():    # exp is Id, CallExpr, ArrayCell
            exptype1 = IntType()
            self.direct_infer(e=ast.expr1, inferred_type=exptype1, c=c)
        if exptype1 != IntType():
            raise TypeMismatchInStatement(ast)     

        # visit conditionExpr (expr2)
        exptype2 = self.visit(ast.expr2, c)
        if exptype2 == TypeCannotInferred():
            raise TypeCannotBeInferred(ast)
        if exptype2 == Unknown():    # exp is Id, CallExpr, ArrayCell
            exptype2 = BoolType()
            self.direct_infer(e=ast.expr2, inferred_type=exptype2, c=c)
        if exptype2 != BoolType():
            raise TypeMismatchInStatement(ast)   

        # visit updateExpr(expr3)
        exptype3 = self.visit(ast.expr3, c)
        if exptype3 == TypeCannotInferred():
            raise TypeCannotBeInferred(ast)
        if exptype3 == Unknown():    # exp is Id, CallExpr, ArrayCell
            exptype3 = IntType()
            self.direct_infer(e=ast.expr3, inferred_type=exptype3, c=c)
        if exptype3 != IntType():
            raise TypeMismatchInStatement(ast)    

        # visit local (For body) var declare
        local_envir = {}
        for vardecl in ast.loop[0]:
            self.visit(vardecl, local_envir)

        # visit local statement
        current_function_name = list(c.keys())[-1]
        total_envir = {**c, **local_envir}
        current_function = {current_function_name : total_envir[current_function_name]}
        del total_envir[current_function_name]
        total_envir = {**total_envir, **current_function}   # append current function to the end of dictionary
        for stmt in ast.loop[1]:
            self.visit(stmt, total_envir)

        # update outer environment
        for name in c:
            if name not in local_envir:
                c[name] = total_envir[name]


    def visitBreak(self,ast, c):
        return Break()

    def visitContinue(self,ast, c):
        return Continue()

    def visitReturn(self,ast, c):
        returntype = VoidType() if ast.expr == None else self.visit(ast.expr, c)
        current_function_name = list(c.keys())[-1]
        current_returntype = c[current_function_name].restype

        # check VoidType
        if returntype == VoidType() and ast.expr != None:
            raise TypeMismatchInStatement(ast)
        if current_returntype == VoidType() and ast.expr != None:
            raise TypeMismatchInStatement(ast)

        # type inference
        current_returntype, returntype = self.mutual_infer(type1=current_returntype, type2=returntype, e2=ast.expr, isStmt=True, isReturnStmt=True, ast=ast)
        # current return type update
        c[current_function_name].restype = current_returntype
        # expr type update 
        self.direct_infer(e=ast.expr, inferred_type=returntype, c=c)


    def visitDowhile(self,ast, c):
        # visit expression
        exptype = self.visit(ast.exp, c)
        if exptype == TypeCannotInferred():
            raise TypeCannotBeInferred(ast)
        if exptype == Unknown():    # exp is Id, CallExpr, ArrayCell
            exptype = BoolType()
            self.direct_infer(e=ast.exp, inferred_type=exptype, c=c)
        if exptype != BoolType():
            raise TypeMismatchInStatement(ast)

        # visit local (DoWhile body) var declare
        local_envir = {}
        for vardecl in ast.sl[0]:
            self.visit(vardecl, local_envir)

        # visit local statement
        current_function_name = list(c.keys())[-1]
        total_envir = {**c, **local_envir}
        current_function = {current_function_name : total_envir[current_function_name]}
        del total_envir[current_function_name]
        total_envir = {**total_envir, **current_function}   # append current function to the end of dictionary
        for stmt in ast.sl[1]:
            self.visit(stmt, total_envir)

        # update outer environment
        for name in c:
            if name not in local_envir:
                c[name] = total_envir[name]


    def visitWhile(self,ast, c):
        # visit expression
        exptype = self.visit(ast.exp, c)
        if exptype == TypeCannotInferred():
            raise TypeCannotBeInferred(ast)
        if exptype == Unknown():    # exp is Id, CallExpr, ArrayCell
            exptype = BoolType()
            self.direct_infer(e=ast.exp, inferred_type=exptype, c=c)
        if exptype != BoolType():
            raise TypeMismatchInStatement(ast)

        # visit local (While body) var declare
        local_envir = {}
        for vardecl in ast.sl[0]:
            self.visit(vardecl, local_envir)

        # visit local statement
        current_function_name = list(c.keys())[-1]
        total_envir = {**c, **local_envir}
        current_function = {current_function_name : total_envir[current_function_name]}
        del total_envir[current_function_name]
        total_envir = {**total_envir, **current_function}   # append current function to the end of dictionary
        for stmt in ast.sl[1]:
            self.visit(stmt, total_envir)

        # update outer environment
        for name in c:
            if name not in local_envir:
                c[name] = total_envir[name]

    def visitCallStmt(self,ast, c):
        if ast.method.name not in c:
            raise Undeclared(Function(), ast.method.name)
        if not isinstance(c[ast.method.name], MType):
            raise Undeclared(Function(), ast.method.name)
        if len(ast.param) != len(c[ast.method.name].intype):
            raise TypeMismatchInStatement(ast)
        for i in range(len(ast.param)):
            type1 = c[ast.method.name].intype[i]    # param type
            type2 = self.visit(ast.param[i], c)     # argument type
            # type inference
            type1, type2 = self.mutual_infer(type1=type1, type2=type2, e2=ast.param[i], isStmt=True, isReturnStmt=False, ast=ast)
            # param type update
            c[ast.method.name].intype[i] = type1
            # argument type update 
            self.direct_infer(e=ast.param[i], inferred_type=type2, c=c)
        
        if c[ast.method.name].restype == Unknown():
            c[ast.method.name].restype = VoidType()
        if c[ast.method.name].restype != VoidType():
            raise TypeMismatchInStatement(ast)


    def visitBinaryOp(self,ast, c):
        typedict = {}
        typedict.update({operator: {'operand_type': IntType(), 'return_type': IntType()} for operator in ['+', '-', '*', '\\', '%']})
        typedict.update({operator: {'operand_type': IntType(), 'return_type': BoolType()} for operator in ['==', '!=', '<', '>', '<=', '>=']})
        typedict.update({operator: {'operand_type': FloatType(), 'return_type': FloatType()} for operator in ['+.', '-.', '*.', '\\.']})
        typedict.update({operator: {'operand_type': FloatType(), 'return_type': BoolType()} for operator in ['=/=', '<.', '>.', '<=.', '>=.']})
        typedict.update({operator: {'operand_type': BoolType(), 'return_type': BoolType()} for operator in ['&&', '||']})
        
        # lhs type inference
        ltype = self.visit(ast.left, c)
        if ltype == TypeCannotInferred():
            return TypeCannotInferred()
        if ltype == Unknown():
            ltype = typedict[ast.op]['operand_type']
            self.direct_infer(e=ast.left, inferred_type=ltype, c=c)

        # rhs type inference
        rtype = self.visit(ast.right, c)
        if rtype == TypeCannotInferred():
            return TypeCannotInferred() 
        if rtype == Unknown():
            rtype = typedict[ast.op]['operand_type']
            self.direct_infer(e=ast.right, inferred_type=rtype, c=c)

        # type checking
        if ltype != typedict[ast.op]['operand_type'] or rtype != typedict[ast.op]['operand_type']:
            raise TypeMismatchInExpression(ast)
        return typedict[ast.op]['return_type']


    def visitUnaryOp(self,ast, c):
        typedict = {
            '-': {'operand_type': IntType(), 'return_type': IntType()},
            '-.': {'operand_type': FloatType(), 'return_type': FloatType()},
            '!': {'operand_type': BoolType(), 'return_type': BoolType()}
        }

        # type inference
        exptype = self.visit(ast.body, c)
        if exptype == TypeCannotInferred():
            return TypeCannotInferred()
        if exptype == Unknown():
            exptype = typedict[ast.op]['operand_type']
            self.direct_infer(e=ast.body, inferred_type=exptype, c=c)

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
            type1 = c[ast.method.name].intype[i]    # param type
            type2 = self.visit(ast.param[i], c)     # argument type
            # type inference
            result = self.mutual_infer(type1=type1, type2=type2, e2=ast.param[i], isStmt=False, isReturnStmt=False, ast=ast)
            if result == TypeCannotInferred():
                return result
            type1, type2 = result
            # param type update
            c[ast.method.name].intype[i] = type1
            # argument type update 
            self.direct_infer(e=ast.param[i], inferred_type=type2, c=c)

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
                indextype = IntType()
                self.direct_infer(e=index, inferred_type=indextype, c=c)
            if indextype != IntType():
                raise TypeMismatchInExpression(ast)
        return self.visit(ast.arr, c)


    def visitId(self,ast, c):
        if ast.name not in c:
            raise Undeclared(Identifier(), ast.name)
        if isinstance(c[ast.name], MType):
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

    
    # Support methods

    def mutual_infer(self, type1, type2, e2, isStmt, isReturnStmt, ast):
        if type1 == Unknown() and type2 == Unknown():
            if isStmt:
                raise TypeCannotBeInferred(ast)
            else:
                return TypeCannotInferred()
        elif type1 == Unknown() and type2 != Unknown():
            if isReturnStmt:
                if isinstance(type2, ArrayType) and type2.eletype == Unknown():
                    raise TypeCannotBeInferred(ast)
                type1 = type2
            else:
                if isinstance(type2, ArrayType):
                    if isStmt:
                        raise TypeMismatchInStatement(ast)
                    else:
                        raise TypeMismatchInExpression(ast)
                type1 = type2
        elif type1 != Unknown() and type2 == Unknown():
            if isinstance(type1, ArrayType):
                if isinstance(e2, CallExpr) and type1.eletype != Unknown():
                    type2 = type1
                else:
                    if isStmt:
                        raise TypeMismatchInStatement(ast)
                    else:
                        raise TypeMismatchInExpression(ast)
            else:
                type2 = type1
        elif type1 != Unknown() and type2 != Unknown():
            if isinstance(type1, ArrayType) and isinstance(type2, ArrayType):
                if type1.dimen != type2.dimen:
                    if isStmt:
                        raise TypeMismatchInStatement(ast)
                    else:
                        raise TypeMismatchInExpression(ast)
                if type1.eletype == Unknown() and type2.eletype == Unknown():
                    if isStmt:
                        raise TypeCannotBeInferred(ast)
                    else:
                        return TypeCannotInferred()
                elif type1.eletype == Unknown() and type2.eletype != Unknown():
                    type1.eletype = type2.eletype
                elif type1.eletype != Unknown() and type2.eletype == Unknown():
                    type2.eletype = type1.eletype
                elif type1.eletype != Unknown() and type2.eletype != Unknown():
                    if type1.eletype != type2.eletype:
                        if isStmt:
                            raise TypeMismatchInStatement(ast)
                        else:
                            raise TypeMismatchInExpression(ast)
            elif isinstance(type1, ArrayType) and not isinstance(type2, ArrayType):
                if isStmt:
                    raise TypeMismatchInStatement(ast)
                else:
                    raise TypeMismatchInExpression(ast)
            elif not isinstance(type1, ArrayType) and isinstance(type2, ArrayType):
                if isStmt:
                    raise TypeMismatchInStatement(ast)
                else:
                    raise TypeMismatchInExpression(ast)
            elif not isinstance(type1, ArrayType) and not isinstance(type2, ArrayType):
                if type1 != type2:
                    if isStmt:
                        raise TypeMismatchInStatement(ast)
                    else:
                        raise TypeMismatchInExpression(ast)
        
        return (type1, type2)

    
    def direct_infer(self, e, inferred_type, c):
        if isinstance(e, Id):
            c[e.name] = inferred_type
        elif isinstance(e, CallExpr):
            c[e.method.name].restype = inferred_type
        elif isinstance(e, ArrayCell):
            if isinstance(e.arr, Id):
                c[e.arr.name].eletype = inferred_type
            elif isinstance(e.arr, CallExpr):
                c[e.arr.method.name].restype.eletype = inferred_type  