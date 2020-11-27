from BKITVisitor import BKITVisitor
from BKITParser import BKITParser
from AST import *
# from tool import *
import functools

class ASTGeneration(BKITVisitor):
    # program  : var_dcl* func_dcl* EOF;
    def visitProgram(self,ctx:BKITParser.ProgramContext):
        # return Program([VarDecl(Id(ctx.ID().getText()),[],None)])
        var_dcl_list = list( functools.reduce(lambda a,b: a+b, map(lambda var_dcl: var_dcl.accept(self), ctx.var_dcl()), []) )
        func_dcl_list = [] if not ctx.func_dcl() else list(map(lambda func_dcl: func_dcl.accept(self), ctx.func_dcl()))
        return Program(var_dcl_list + func_dcl_list) 

    # var_dcl : VAR COLON var_init (COMMA var_init)* SEMI;
    def visitVar_dcl(self,ctx:BKITParser.Var_dclContext):   # return List[VarDecl()] in one variable declaration line
        return list(map(lambda var_init: var_init.accept(self), ctx.var_init()))

    # var_init : var (ASSIGN_OP literal)?; 
    def visitVar_init(self,ctx:BKITParser.Var_initContext): # return one VarDecl() object (each VarDecl() is one variable)
        ident, intlit_list = ctx.var().accept(self)
        return VarDecl(ident, intlit_list, None if not ctx.literal() else ctx.literal().accept(self))

    # var : ID (LSB INTLIT RSB)*;
    def visitVar(self,ctx:BKITParser.VarContext):   # return Id, List[int]
        return Id(ctx.ID().getText()), [] if not ctx.INTLIT() else list(map(lambda intlit: int(intlit.getText(), 0), ctx.INTLIT()))

    # func_dcl : FUNCTION COLON ID param_list? body ;
    def visitFunc_dcl(self,ctx:BKITParser.Func_dclContext): # return one FuncDecl() object
        return FuncDecl(Id(ctx.ID().getText()), [] if not ctx.param_list() else ctx.param_list().accept(self), ctx.body().accept(self))

    # param_list : PARAMETER COLON param (COMMA param)*; 
    def visitParam_list(self,ctx:BKITParser.Param_listContext): # return List[VarDecl]
        return list(map(lambda param: param.accept(self), ctx.param()))

    # param : ID (LSB INTLIT RSB)*;
    def visitParam(self,ctx:BKITParser.ParamContext):   # return one VarDecl() object
        return VarDecl(Id(ctx.ID().getText()), [] if not ctx.INTLIT() else list(map(lambda intlit: int(intlit.getText(), 0), ctx.INTLIT())), None)

    # body : BODY COLON statement_list END_BODY DOT;
    def visitBody(self,ctx:BKITParser.BodyContext):
        return ctx.statement_list().accept(self)

    # statement_list : var_dcl* statement*;
    def visitStatement_list(self,ctx:BKITParser.Statement_listContext): # return Tuple(List[VarDecl], List[Stmt])
        var_dcl_list = list( functools.reduce(lambda a,b: a+b, map(lambda var_dcl: var_dcl.accept(self), ctx.var_dcl()), []) )
        stmt_list = [] if not ctx.statement() else list(map(lambda stmt: stmt.accept(self), ctx.statement()))
        return (var_dcl_list, stmt_list)

    # statement : assign_stmt | if_stmt | for_stmt | while_stmt | do_while_stmt | call_stmt | return_stmt | break_stmt | continue_stmt;
    def visitStatement(self,ctx:BKITParser.StatementContext):
        return ctx.getChild(0).accept(self)

    # assign_stmt : lhs ASSIGN_OP expression SEMI;
    def visitAssign_stmt(self,ctx:BKITParser.Assign_stmtContext):   # return Assign() object
        return Assign(ctx.lhs().accept(self), ctx.expression().accept(self))

    # lhs : ID | exp7 (LSB expression RSB)+;  // lhs is scala variable or index expression;
    def visitLhs(self,ctx:BKITParser.LhsContext):   # return Id() or ArrayCell() object
        return Id(ctx.ID().getText()) if not ctx.expression() else ArrayCell(ctx.exp7().accept(self), list(map(lambda expression: expression.accept(self), ctx.expression())))

    # if_stmt : if_then_part elif_then_part* else_part? END_IF DOT;
    def visitIf_stmt(self,ctx:BKITParser.If_stmtContext):   # return If() object
        ifthenStmt = [ctx.if_then_part().accept(self)] + ([] if not ctx.elif_then_part() else list(map(lambda elif_then_part: elif_then_part.accept(self), ctx.elif_then_part())))
        elseStmt = ([],[]) if not ctx.else_part() else ctx.else_part().accept(self)
        return If(ifthenStmt, elseStmt)

    # if_then_part : IF expression THEN statement_list;
    def visitIf_then_part(self,ctx:BKITParser.If_then_partContext):
        (var_dcl_list, stmt_list) = ctx.statement_list().accept(self)
        return (ctx.expression().accept(self), var_dcl_list, stmt_list)

    # elif_then_part : ELSE_IF expression THEN statement_list;
    def visitElif_then_part(self,ctx:BKITParser.Elif_then_partContext):
        (var_dcl_list, stmt_list) = ctx.statement_list().accept(self)
        return (ctx.expression().accept(self), var_dcl_list, stmt_list)

    # else_part : ELSE statement_list;
    def visitElse_part(self,ctx:BKITParser.Else_partContext):
        return ctx.statement_list().accept(self)

    # for_stmt : FOR LP ID ASSIGN_OP expression COMMA expression COMMA expression RP DO statement_list END_FOR DOT;
    def visitFor_stmt(self,ctx:BKITParser.For_stmtContext): # return For object
        return For(Id(ctx.ID().getText()), ctx.expression(0).accept(self), ctx.expression(1).accept(self), ctx.expression(2).accept(self), ctx.statement_list().accept(self))

    # while_stmt : WHILE expression DO statement_list END_WHILE DOT;
    def visitWhile_stmt(self,ctx:BKITParser.While_stmtContext): # return While() object
        return While(ctx.expression().accept(self), ctx.statement_list().accept(self))

    # do_while_stmt : DO statement_list WHILE expression END_DO DOT;
    def visitDo_while_stmt(self,ctx:BKITParser.Do_while_stmtContext):   # return Dowhile() object
        return Dowhile(ctx.statement_list().accept(self), ctx.expression().accept(self))

    # break_stmt : BREAK SEMI;
    def visitBreak_stmt(self,ctx:BKITParser.Break_stmtContext): # return Break() object
        return Break()

    # continue_stmt : CONTINUE SEMI;
    def visitContinue_stmt(self,ctx:BKITParser.Continue_stmtContext):   # return Continue() object
        return Continue()

    # call_stmt : func_call SEMI;
    def visitCall_stmt(self,ctx:BKITParser.Call_stmtContext):   # return CallStmt() object
        func_call = ctx.func_call().accept(self)
        return CallStmt(func_call.method, func_call.param)

    # func_call : ID LP (expression (COMMA expression)*)? RP;
    def visitFunc_call(self,ctx:BKITParser.Func_callContext):   # return CallExpr() object
        return CallExpr(Id(ctx.ID().getText()), [] if not ctx.expression() else list(map(lambda expression: expression.accept(self), ctx.expression())))

    # return_stmt : RETURN expression? SEMI;
    def visitReturn_stmt(self,ctx:BKITParser.Return_stmtContext):   # return Return() object
        return Return(None if not ctx.expression() else ctx.expression().accept(self))

    # expression :
    # exp1 (EQ_OP | INT_NEQ_OP | FLOAT_NEQ_OP | INT_LT_OP | FLOAT_LT_OP | INT_GT_OP | FLOAT_GT_OP | INT_LTE_OP | FLOAT_LTE_OP | INT_GTE_OP | FLOAT_GTE_OP) exp1   // relational
    # | exp1;
    def visitExpression(self,ctx:BKITParser.ExpressionContext):
        return ctx.exp1(0).accept(self) if ctx.getChildCount() == 1 else BinaryOp(ctx.getChild(1).getText(), ctx.exp1(0).accept(self), ctx.exp1(1).accept(self))

    # exp1 : exp1 (CONJ_OP | DISJ_OP) exp2 // logical
    # | exp2;
    def visitExp1(self,ctx:BKITParser.Exp1Context):
        return ctx.exp2().accept(self) if ctx.getChildCount() == 1 else BinaryOp(ctx.getChild(1).getText(), ctx.exp1().accept(self), ctx.exp2().accept(self))

    # exp2 : exp2 (INT_ADD_OP | FLOAT_ADD_OP | INT_SUB_OP | FLOAT_SUB_OP) exp3 // adding
    # | exp3;
    def visitExp2(self,ctx:BKITParser.Exp2Context):
        return ctx.exp3().accept(self) if ctx.getChildCount() == 1 else BinaryOp(ctx.getChild(1).getText(), ctx.exp2().accept(self), ctx.exp3().accept(self))

    # exp3 : exp3 (INT_MUL_OP | FLOAT_MUL_OP | INT_DIV_OP | FLOAT_DIV_OP | INT_REMAINDER_OP) exp4 // multiplying
    # | exp4;
    def visitExp3(self,ctx:BKITParser.Exp3Context):
        return ctx.exp4().accept(self) if ctx.getChildCount() == 1 else BinaryOp(ctx.getChild(1).getText(), ctx.exp3().accept(self), ctx.exp4().accept(self))

    # exp4 : NEG_OP exp4   // logical
    # | exp5;
    def visitExp4(self,ctx:BKITParser.Exp4Context):
        return ctx.exp5().accept(self) if ctx.getChildCount() == 1 else UnaryOp(ctx.getChild(0).getText(), ctx.exp4().accept(self))

    # exp5 : (INT_SUB_OP | FLOAT_SUB_OP) exp5  // sign
    # | exp6;
    def visitExp5(self,ctx:BKITParser.Exp5Context):
        return ctx.exp6().accept(self) if ctx.getChildCount() == 1 else UnaryOp(ctx.getChild(0).getText(), ctx.exp5().accept(self))

    # exp6 : exp7 (LSB expression RSB)+   // index expression: (ID | func_call) or exp7 ???
    # | exp7;
    def visitExp6(self,ctx:BKITParser.Exp6Context):
        return ctx.exp7().accept(self) if ctx.getChildCount() == 1 else ArrayCell(ctx.exp7().accept(self), list(map(lambda exp: exp.accept(self), ctx.expression())))

    # exp7 : LP expression RP
    # | func_call // function call : assoc none ?????
    # | (ID | literal) ; // operands
    def visitExp7(self,ctx:BKITParser.Exp7Context):
        if ctx.expression():
            return ctx.expression().accept(self)
        elif ctx.func_call():
            return ctx.func_call().accept(self)
        elif ctx.ID():
            return Id(ctx.ID().getText())
        else:
            return ctx.literal().accept(self)

    # arraylit : LCB (literal (COMMA literal)*)? RCB;
    def visitArraylit(self,ctx:BKITParser.Return_stmtContext):
        return ArrayLiteral(list(map(lambda literal: literal.accept(self), ctx.literal())))

    # literal : INTLIT | FLOATLIT | BOOLEANLIT | STRINGLIT | arraylit;
    def visitLiteral(self,ctx:BKITParser.Return_stmtContext):
        if ctx.INTLIT():
            value = ctx.INTLIT().getText()
            return IntLiteral(int(value, 16 if ('x' in value) or ('X' in value) else 8 if ('o' in value) or ('O' in value) else 10))
        elif ctx.FLOATLIT():
            return FloatLiteral(float(ctx.FLOATLIT().getText()))
        elif ctx.BOOLEANLIT():
            return BooleanLiteral(ctx.BOOLEANLIT().getText() == 'True')
        elif ctx.STRINGLIT():
            return StringLiteral(ctx.STRINGLIT().getText())
        elif ctx.arraylit():
            return ctx.arraylit().accept(self)