
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
from copy import deepcopy

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
    isinvoked: bool = False
    notReturn: bool = False

@dataclass
class TypeCannotInferred:
    value: str = 'type cannnot inferred'

@dataclass
class Result:
    breakcontinue: str = "" # "break" for Break(), "continue" for Continue()
    hasreturn: bool = False # check Return stmt, loop has return, if has all path return
    terminate: bool = False # check unreachable stmt


@dataclass
class Symbol:
    name: str
    mtype:Type

class StaticChecker(BaseVisitor):
    def __init__(self,ast):
        self.ast = ast
        self.global_envi = [
Symbol("int_of_float",MType([FloatType()],IntType())),
Symbol("float_to_int",MType([IntType()],FloatType())),
Symbol("int_of_string",MType([StringType()],IntType())),
Symbol("string_of_int",MType([IntType()],StringType())),
Symbol("float_of_string",MType([StringType()],FloatType())),
Symbol("string_of_float",MType([FloatType()],StringType())),
Symbol("bool_of_string",MType([StringType()],BoolType())),
Symbol("string_of_bool",MType([BoolType()],StringType())),
Symbol("read",MType([],StringType())),
Symbol("printLn",MType([],VoidType())),
Symbol("print",MType([StringType()],VoidType())),
Symbol("printStrLn",MType([StringType()],VoidType()))]                      
   
    def check(self):
        return self.visit(self.ast,self.global_envi)

    def visitProgram(self,ast, c):
        for symbol in c:
            symbol.mtype.isinvoked = True

        for decl in ast.decl:
            if isinstance(decl, VarDecl):
                self.visit(decl, c)
            else:
                funcname = decl.name.name
                intype_lst = []
                if funcname in self.nameList(c):
                    raise Redeclared(Function(), funcname)
                for param in decl.param:
                    paramtype = Unknown() if param.varDimen == [] else ArrayType(deepcopy(param.varDimen), Unknown())
                    intype_lst.append(paramtype)
                c.append(Symbol(funcname, MType(intype_lst, Unknown())))

        if ('main' not in self.nameList(c)) or (not isinstance(self.symbol('main', c).mtype, MType)):
            raise NoEntryPoint()
                
        for decl in ast.decl:
            if isinstance(decl, FuncDecl):
                self.visit(decl, c)

        # check unreachable function
        for symbol in c:
            if isinstance(symbol.mtype, MType) and symbol.name != 'main':
                if symbol.mtype.isinvoked == False:
                    raise UnreachableFunction(symbol.name)


    def visitVarDecl(self,ast, c):
        idname = ast.variable.name
        if idname in self.nameList(c):
            raise Redeclared(Variable(), idname)
        idtype = Unknown() if not ast.varInit else self.visit(ast.varInit, c)
        if ast.varDimen != []:  # array type
            if idtype == Unknown():
                idtype = ArrayType(deepcopy(ast.varDimen), Unknown())
            else:
                if ast.varDimen != idtype.dimen:
                    raise TypeMismatchInExpression(ast.varInit) # ???
        else:   # scalar type
            if isinstance(idtype, ArrayType):
                raise TypeMismatchInExpression(ast.varInit) # ???
        c.append(Symbol(idname, idtype))


    def visitFuncDecl(self,ast, c):
        # visit param
        param_envir = []
        for param in ast.param:
            paramname = param.variable.name
            if paramname in self.nameList(param_envir):
                raise Redeclared(Parameter(), paramname)
            paramtype = Unknown() if param.varDimen == [] else ArrayType(deepcopy(param.varDimen), Unknown())
            param_envir.append(Symbol(paramname, paramtype))
      
        # update param of this function from outer environment
        for index in range(len(param_envir)):
            param_envir[index].mtype = self.symbol(ast.name.name, c).mtype.intype[index]

        # visit local var declare
        local_envir = deepcopy(param_envir)
        for vardecl in ast.body[0]:
            self.visit(vardecl, local_envir)
        
        # visit statement
        total_envir = deepcopy(local_envir)
        for name in self.nameList(c):
            if name not in self.nameList(local_envir):
                total_envir.append(self.symbol(name,c))


        total_envir.append(Symbol("Current Function", self.symbol(ast.name.name, c).mtype))
        current_function = self.symbol(ast.name.name, total_envir)
        del total_envir[self.index(ast.name.name, total_envir)]
        total_envir.append(current_function)   # append current function to the end of dictionary
        # visit stmt
        hasreturn = False
        for i in range(len(ast.body[1])):
            stmt = ast.body[1][i]
            result = self.visit(stmt, total_envir)

            if result.breakcontinue:   # check not in loop
                raise NotInLoop(Break() if result.breakcontinue == "break" else Continue())

            if result.terminate:    # check unreachable stmt
                if i < len(ast.body[1]) - 1:
                    raise UnreachableStatement(ast.body[1][i+1])

            if result.hasreturn: # check function not return
                hasreturn = True

            # type inference for function parameters
            if isinstance(total_envir[-1].mtype, MType): # current function is not hiden in local scope (by same name variable)
                for index in range(len(param_envir)):
                    type1 = total_envir[index].mtype
                    type2 = self.symbol(total_envir[-1].name, total_envir).mtype.intype[index]
                    type1, type2 = self.mutual_infer(type1=type1, type2=type2, e2=None, isStmt=False, isReturnStmt=False, acceptdoubleUnknown=True, ast=ast)
                    total_envir[index].mtype = type1
                    self.symbol(total_envir[-1].name, total_envir).mtype.intype[index] = type2

                    self.symbol("Current Function", total_envir).mtype.intype[index] = type2

        # update global environment
        for name in self.nameList(c):
            if name not in self.nameList(local_envir):
                self.symbol(name, c).mtype = self.symbol(name, total_envir).mtype
            else:
                if not isinstance(self.symbol(total_envir[-1].name, total_envir).mtype, MType):
                    self.symbol(total_envir[-1].name, c).mtype.restype = self.symbol("Current Function", total_envir).mtype.restype

        # check function not return
        if self.symbol(total_envir[-1].name, c).mtype.restype == Unknown():
            self.symbol(total_envir[-1].name, c).mtype.restype = VoidType()
        else:
            if not hasreturn:
                if self.symbol(total_envir[-1].name, c).mtype.restype != VoidType():
                    raise FunctionNotReturn(total_envir[-1].name)


    def visitAssign(self,ast, c):   # left hand side can be in any type except VoidType
        ltype = self.visit(ast.lhs, c)
        rtype = self.visit(ast.rhs, c)
        ltype = self.visit(ast.lhs, c)
        if ltype == TypeCannotInferred() or rtype == TypeCannotInferred():
            raise TypeCannotBeInferred(ast)
        if ltype == VoidType() or rtype == VoidType():
            raise TypeMismatchInStatement(ast)

        # type inference
        result = self.mutual_infer(type1=ltype, type2=rtype, e2=ast.rhs, isStmt=True, isReturnStmt=False, acceptdoubleUnknown=False, ast=ast)
        if result == TypeCannotInferred():
            raise TypeCannotBeInferred(ast)
        ltype, rtype = result
        # lhs type update
        self.direct_infer(e=ast.lhs, inferred_type=ltype, c=c)
        # rhs type update
        self.direct_infer(e=ast.rhs, inferred_type=rtype, c=c)

        return Result()

        

    def visitIf(self,ast, c):
        result = Result()   # used to store break/continue and return
        return_count = 0    # used to check all path of if have return
        breakcontinue_lst = []
        terminate_count = 0 # used to check all path of if have terminate signal (break, continue, return)
        current_function_name = c[-1].name
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
            local_envir = []
            for vardecl in ifthenstmt[1]:
                self.visit(vardecl, local_envir)

            # visit if/elif statement
            total_envir = deepcopy(c)
            for name in self.nameList(local_envir):
                if name in self.nameList(c):
                    self.symbol(name, total_envir).mtype = self.symbol(name, local_envir).mtype
                else:
                    total_envir.append(self.symbol(name, local_envir))
            current_function = self.symbol(current_function_name, total_envir)
            del total_envir[self.index(current_function_name, total_envir)]
            total_envir.append(current_function)   # append current function to the end of dictionary

            localterminate = False
            # visit stmt
            for i in range(len(ifthenstmt[2])):
                stmt = ifthenstmt[2][i]
                temp_result = self.visit(stmt, total_envir)
                if temp_result.terminate:    
                    if i < len(ifthenstmt[2]) - 1:
                        raise UnreachableStatement(ifthenstmt[2][i+1])
                    localterminate = True

                if temp_result.breakcontinue:
                    breakcontinue_lst.append(Break() if temp_result.breakcontinue == "break" else Continue())

                if temp_result.hasreturn:
                    return_count += 1
                    localterminate = True
            if localterminate:
                terminate_count += 1

            # update outer environment
            for name in self.nameList(c):
                if name not in self.nameList(local_envir):
                    self.symbol(name, c).mtype = self.symbol(name, total_envir).mtype
        
        # visit else local var declare
        local_envir = []
        for vardecl in ast.elseStmt[0]:
            self.visit(vardecl, local_envir)

        # visit else statement
        total_envir = deepcopy(c)
        for name in self.nameList(local_envir):
            if name in self.nameList(c):
                self.symbol(name, total_envir).mtype = self.symbol(name, local_envir).mtype
            else:
                total_envir.append(self.symbol(name, local_envir))
        current_function = self.symbol(current_function_name, total_envir)
        del total_envir[self.index(current_function_name, total_envir)]
        total_envir.append(current_function)   # append current function to the end of dictionary

        localterminate = False
        # visit stmt
        for i in range(len(ast.elseStmt[1])):
            stmt = ast.elseStmt[1][i]
            temp_result = self.visit(stmt, total_envir)
            if temp_result.terminate:
                if i < len(ast.elseStmt[1]) - 1:
                    raise UnreachableStatement(ast.elseStmt[1][i+1])
                localterminate = True

            if temp_result.breakcontinue:
                breakcontinue_lst.append(Break() if temp_result.breakcontinue == "break" else Continue())
               
            if temp_result.hasreturn:
                return_count += 1
                localterminate = True
        if localterminate:
            terminate_count += 1
        
        # update outer environment
        for name in self.nameList(c):
            if name not in self.nameList(local_envir):
                self.symbol(name, c).mtype = self.symbol(name, total_envir).mtype

       
        # update result
        if len(breakcontinue_lst) != 0:
            result.breakcontinue = "break" if isinstance(breakcontinue_lst[0], Break) else "continue"
        else:
            result.breakcontinue = ""

        result.hasreturn = True if return_count == len(ast.ifthenStmt) + 1 else False

        result.terminate = True if terminate_count == len(ast.ifthenStmt) + 1 else False

        return result
    

    def visitFor(self,ast, c):
        # visit scalar variable
        indextype = self.visit(ast.idx1, c)
        if indextype == Unknown():
            indextype = IntType()
            self.symbol(ast.idx1.name, c).mtype = indextype
        if indextype != IntType():
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
        local_envir = []
        for vardecl in ast.loop[0]:
            self.visit(vardecl, local_envir)

        # visit local statement
        total_envir = deepcopy(c)
        for name in self.nameList(local_envir):
            if name in self.nameList(c):
                self.symbol(name, total_envir).mtype = self.symbol(name, local_envir).mtype
            else:
                total_envir.append(self.symbol(name, local_envir))
        current_function_name = c[-1].name
        current_function = self.symbol(current_function_name, total_envir)
        del total_envir[self.index(current_function_name, total_envir)]
        total_envir.append(current_function)   # append current function to the end of dictionary
        result = Result() # used to store break/continue and return
        # visit stmt
        for i in range(len(ast.loop[1])):
            stmt = ast.loop[1][i]
            temp_result = self.visit(stmt, total_envir)
            if temp_result.terminate:
                if i < len(ast.loop[1]) - 1:
                    raise UnreachableStatement(ast.loop[1][i+1])

            if temp_result.hasreturn:
                result.hasreturn = True
                result.terminate = True

        # update outer environment
        for name in self.nameList(c):
            if name not in self.nameList(local_envir):
                self.symbol(name, c).mtype = self.symbol(name, total_envir).mtype

        return result


    def visitBreak(self,ast, c):
        return Result("break", False, True)

    def visitContinue(self,ast, c):
        return Result("continue", False, True)

    def visitReturn(self,ast, c):
        returntype = VoidType() if ast.expr == None else self.visit(ast.expr, c)
        current_returntype = self.symbol("Current Function", c).mtype.restype

        # check VoidType
        if returntype == VoidType() and ast.expr != None:
            raise TypeMismatchInStatement(ast)
        if current_returntype == VoidType() and ast.expr != None:
            raise TypeMismatchInStatement(ast)

        # type inference
        current_returntype, returntype = self.mutual_infer(type1=current_returntype, type2=returntype, e2=ast.expr, isStmt=True, isReturnStmt=True, acceptdoubleUnknown=False, ast=ast)
        # current return type update
        self.symbol("Current Function", c).mtype.restype = current_returntype
        if isinstance(c[-1].mtype, MType):
            self.symbol(c[-1].name, c).mtype.restype = current_returntype
        # expr type update 
        self.direct_infer(e=ast.expr, inferred_type=returntype, c=c)

        return Result("", True, True)


    def visitDowhile(self,ast, c):
        # visit local (DoWhile body) var declare
        local_envir = []
        for vardecl in ast.sl[0]:
            self.visit(vardecl, local_envir)

        # visit local statement
        total_envir = deepcopy(c)
        for name in self.nameList(local_envir):
            if name in self.nameList(c):
                self.symbol(name, total_envir).mtype = self.symbol(name, local_envir).mtype
            else:
                total_envir.append(self.symbol(name, local_envir))
        current_function_name = c[-1].name
        current_function = self.symbol(current_function_name, total_envir)
        del total_envir[self.index(current_function_name, total_envir)]
        total_envir.append(current_function)   # append current function to the end of dictionary
        result = Result() # used to store break/continue and return
        # visit stmt
        for i in range(len(ast.sl[1])):
            stmt = ast.sl[1][i]
            temp_result = self.visit(stmt, total_envir)
            if temp_result.terminate:
                if i < len(ast.sl[1]) - 1:
                    raise UnreachableStatement(ast.sl[1][i+1])

            if temp_result.hasreturn:
                result.hasreturn = True
                result.terminate = True

        # update outer environment
        for name in self.nameList(c):
            if name not in self.nameList(local_envir):
                self.symbol(name, c).mtype = self.symbol(name, total_envir).mtype

        # visit expression
        exptype = self.visit(ast.exp, c)
        if exptype == TypeCannotInferred():
            raise TypeCannotBeInferred(ast)
        if exptype == Unknown():    # exp is Id, CallExpr, ArrayCell
            exptype = BoolType()
            self.direct_infer(e=ast.exp, inferred_type=exptype, c=c)
        if exptype != BoolType():
            raise TypeMismatchInStatement(ast)

        return result


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
        local_envir = []
        for vardecl in ast.sl[0]:
            self.visit(vardecl, local_envir)

        # visit local statement
        total_envir = deepcopy(c)
        for name in self.nameList(local_envir):
            if name in self.nameList(c):
                self.symbol(name, total_envir).mtype = self.symbol(name, local_envir).mtype
            else:
                total_envir.append(self.symbol(name, local_envir))
        current_function_name = c[-1].name
        current_function = self.symbol(current_function_name, total_envir)
        del total_envir[self.index(current_function_name, total_envir)]
        total_envir.append(current_function)   # append current function to the end of dictionary
        result = Result() # used to store break/continue and return
        # visit stmt
        for i in range(len(ast.sl[1])):
            stmt = ast.sl[1][i]
            temp_result = self.visit(stmt, total_envir)
            if temp_result.terminate:
                if i < len(ast.sl[1]) - 1:
                    raise UnreachableStatement(ast.sl[1][i+1])

            if temp_result.hasreturn:
                result.hasreturn = True
                result.terminate = True

        # update outer environment
        for name in self.nameList(c):
            if name not in self.nameList(local_envir):
                self.symbol(name, c).mtype = self.symbol(name, total_envir).mtype

        return result

    def visitCallStmt(self,ast, c):
        if ast.method.name not in self.nameList(c):
            raise Undeclared(Function(), ast.method.name)
        if not isinstance(self.symbol(ast.method.name, c).mtype, MType):
            raise Undeclared(Function(), ast.method.name)
        if len(ast.param) != len(self.symbol(ast.method.name, c).mtype.intype):
            raise TypeMismatchInStatement(ast)
        for i in range(len(ast.param)):
            # type1 = c[ast.method.name].intype[i]    # param type
            type2 = self.visit(ast.param[i], c)     # argument type
            if type2 == TypeCannotInferred():
                raise TypeCannotBeInferred(ast)
            type1 = self.symbol(ast.method.name, c).mtype.intype[i]    # param type
            # type inference
            result = self.mutual_infer(type1=type1, type2=type2, e2=ast.param[i], isStmt=True, isReturnStmt=False, acceptdoubleUnknown=False, ast=ast)
            if result == TypeCannotInferred():
                raise TypeCannotBeInferred(ast)
            type1, type2 = result
            # param type update
            self.symbol(ast.method.name, c).mtype.intype[i] = type1
            # argument type update 
            self.direct_infer(e=ast.param[i], inferred_type=type2, c=c)

            # if func call inside the same func declare
            # update param of declared function in every agument iteration
            if ast.method.name == c[-1].name and isinstance(c[-1].mtype, MType):
                for j in range(len(ast.param)):
                    type1 = self.symbol(ast.method.name, c).mtype.intype[j]
                    type2 = c[j].mtype
                    self.symbol(ast.method.name, c).mtype.intype[j], c[j].mtype = self.mutual_infer(type1=type1, type2=type2, e2=None, isStmt=True, isReturnStmt=False, acceptdoubleUnknown=True, ast=ast)

                    self.symbol("Current Function", c).mtype.intype[j] = self.symbol(ast.method.name, c).mtype.intype[j]

        # check/infer return type
        if self.symbol(ast.method.name, c).mtype.restype == Unknown():
            self.symbol(ast.method.name, c).mtype.restype = VoidType()
        if self.symbol(ast.method.name, c).mtype.restype != VoidType():
            raise TypeMismatchInStatement(ast)
        
        if ast.method.name != c[-1].name:   # if it is not call by itself
            self.symbol(ast.method.name, c).mtype.isinvoked = True

        return Result()


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
        if ast.method.name not in self.nameList(c):
            raise Undeclared(Function(), ast.method.name)
        if not isinstance(self.symbol(ast.method.name, c).mtype, MType):
            raise Undeclared(Function(), ast.method.name)
        if len(ast.param) != len(self.symbol(ast.method.name, c).mtype.intype):
            raise TypeMismatchInExpression(ast)
        for i in range(len(ast.param)):
            # type1 = self.symbol(ast.method.name, c).mtype.intype[i]    # param type
            type2 = self.visit(ast.param[i], c)     # argument type
            if type2 == TypeCannotInferred():
                return TypeCannotInferred()
            type1 = self.symbol(ast.method.name, c).mtype.intype[i]    # param type
            # type inference
            result = self.mutual_infer(type1=type1, type2=type2, e2=ast.param[i], isStmt=False, isReturnStmt=False, acceptdoubleUnknown=False, ast=ast)
            if result == TypeCannotInferred():
                return TypeCannotInferred()
            type1, type2 = result
            # param type update
            self.symbol(ast.method.name, c).mtype.intype[i] = type1
            # argument type update 
            self.direct_infer(e=ast.param[i], inferred_type=type2, c=c)

            # if func call inside the same func declare
            # update param of declared function in every agument iteration
            if ast.method.name == c[-1].name and isinstance(c[-1].mtype, MType):
                for j in range(len(ast.param)):
                    type1 = self.symbol(ast.method.name, c).mtype.intype[j]
                    type2 = c[j].mtype
                    self.symbol(ast.method.name, c).mtype.intype[j], c[j].mtype = self.mutual_infer(type1=type1, type2=type2, e2=None, isStmt=False, isReturnStmt=False, acceptdoubleUnknown=True, ast=ast)

                    self.symbol("Current Function", c).mtype.intype[j] = self.symbol(ast.method.name, c).mtype.intype[j]
            
        if ast.method.name != c[-1].name:   # if it is not call by itself
            self.symbol(ast.method.name, c).mtype.isinvoked = True
        return self.symbol(ast.method.name, c).mtype.restype

    # check Undeclare, check index
    # return innermost eletype
    def visitArrayCell(self,ast, c):
        arrtype = self.visit(ast.arr, c)
        if arrtype == TypeCannotInferred():
            return TypeCannotInferred()

        if not isinstance(arrtype, ArrayType):
            if isinstance(ast.arr, Id):
                raise TypeMismatchInExpression(ast)
            if isinstance(ast.arr, CallExpr):
                if isinstance(arrtype, Unknown):
                    return TypeCannotInferred() # or ArrayType([None]*len(ast.idx), Unknown()) ???
                else:
                    raise TypeMismatchInExpression(ast)
        if len(arrtype.dimen) != len(ast.idx):
            raise TypeMismatchInExpression(ast)

        for i in range(len(ast.idx)):
            index = ast.idx[i]
            indextype = self.visit(index, c)
            if indextype == TypeCannotInferred():
                return TypeCannotInferred()
            if indextype == Unknown():  # index is Id or CallExpr or ArrayCell
                indextype = IntType()
                self.direct_infer(e=index, inferred_type=indextype, c=c)
            if indextype != IntType():
                raise TypeMismatchInExpression(ast)

            # check index out of range
            result = self.eval_const_expr(index)
            if result != None:
                if result < 0 or result >= arrtype.dimen[i]:
                    raise IndexOutOfRange(ast)

        return self.visit(ast.arr, c).eletype


    def visitId(self,ast, c):
        if ast.name not in self.nameList(c):
            raise Undeclared(Identifier(), ast.name)
        if isinstance(self.symbol(ast.name, c).mtype, MType):
            raise Undeclared(Identifier(), ast.name)
        return self.symbol(ast.name, c).mtype


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
    def symbol(self, name, lst):
        for symbol in lst:
            if symbol.name == name:
                return symbol
        return None

    def index(self, name, lst):
        for index in range(len(lst)):
            if lst[index].name == name:
                return index
        return None

    def nameList(self, lst):
        return [symbol.name for symbol in lst]


    def mutual_infer(self, type1, type2, e2, isStmt, isReturnStmt, acceptdoubleUnknown, ast):
        if type1 == Unknown() and type2 == Unknown():
            if not acceptdoubleUnknown:
                if isStmt:
                    raise TypeCannotBeInferred(ast)
                else:
                    return TypeCannotInferred()
        elif type1 == Unknown() and type2 != Unknown():
            if isReturnStmt:
                if not acceptdoubleUnknown:
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
                if isinstance(e2, CallExpr):
                    if type1.eletype != Unknown():
                        type2 = type1
                    else:
                        return TypeCannotInferred()
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
                    if not acceptdoubleUnknown:
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
            self.symbol(e.name, c).mtype = inferred_type
        elif isinstance(e, CallExpr):
            self.symbol(e.method.name, c).mtype.restype = inferred_type
        elif isinstance(e, ArrayCell):
            if isinstance(e.arr, Id):
                self.symbol(e.arr.name, c).mtype.eletype = inferred_type
            elif isinstance(e.arr, CallExpr):
                self.symbol(e.arr.method.name, c).mtype.restype.eletype = inferred_type  

    
    def eval_const_expr(self, expr):
        if isinstance(expr, BinaryOp):
            left = self.eval_const_expr(expr.left)
            right = self.eval_const_expr(expr.right)
            if left == None or right == None:
                return None
            if expr.op == '+':
                return left + right
            elif expr.op == '-':
                return left - right
            elif expr.op == '*':
                return left * right
            elif expr.op == '\\':
                return left // right
            elif expr.op == '%':
                return left % right
            else:
                return None
        elif isinstance(expr, UnaryOp):
            body = self.eval_const_expr(expr.body)
            if body == None:
                return None
            if expr.op == '-':
                return - body
            else:
                return None
        elif isinstance(expr, IntLiteral):
            return expr.value
        else:
            return None