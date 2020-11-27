// MSSV : 1810283


grammar BKIT;

@lexer::header {
from lexererr import *
}

@lexer::members {
def emit(self):
    tk = self.type
    result = super().emit()
    if tk == self.UNCLOSE_STRING:       
        raise UncloseString(result.text)   
    elif tk == self.ILLEGAL_ESCAPE:
        raise IllegalEscape(result.text)    
    elif tk == self.ERROR_CHAR:
        raise ErrorToken(result.text)
    elif tk == self.UNTERMINATED_COMMENT:
        raise UnterminatedComment()
    else:
        return result
}

options{
	language=Python3;
}

// program
program  : var_dcl* func_dcl* EOF;

// variable declaration
var_dcl : VAR COLON var_init (COMMA var_init)* SEMI;

var_init : var (ASSIGN_OP literal)?; 

var : ID (LSB INTLIT RSB)*;
// function declaration
func_dcl : FUNCTION COLON ID param_list? body ;

param_list : PARAMETER COLON param (COMMA param)*; 

param : ID (LSB INTLIT RSB)*;   // (LSB INTLIT RSB)* ???

body : BODY COLON statement_list END_BODY DOT; // why separate statement_list or var_dcl* statement*

statement_list : var_dcl* statement*;

// statements
statement : assign_stmt | if_stmt | for_stmt | while_stmt | do_while_stmt | call_stmt | return_stmt | break_stmt | continue_stmt;

assign_stmt : lhs ASSIGN_OP expression SEMI;

// lhs : ID (LSB expression RSB)*;  // lhs is (scala variable | index expression) or ID[expression]*   ???

lhs : ID | exp7 (LSB expression RSB)+;  // lhs is scala variable or index expression;

if_stmt : if_then_part elif_then_part* else_part? END_IF DOT;

if_then_part : IF expression THEN statement_list;

elif_then_part : ELSE_IF expression THEN statement_list;

else_part : ELSE statement_list;

for_stmt : FOR LP ID ASSIGN_OP expression COMMA expression COMMA expression RP DO statement_list END_FOR DOT;

while_stmt : WHILE expression DO statement_list END_WHILE DOT;

do_while_stmt : DO statement_list WHILE expression END_DO DOT;

break_stmt : BREAK SEMI;

continue_stmt : CONTINUE SEMI;

call_stmt : func_call SEMI;

func_call : ID LP (expression (COMMA expression)*)? RP;

return_stmt : RETURN expression? SEMI;

// expression
// expression : 
//     LP expression RP
//     | func_call // function call : assoc none ?????
//     | ID (LSB expression RSB)+ // index : arraylit[expression] ??????
//     | <assoc=right> (INT_SUB_OP | FLOAT_SUB_OP) expression  // sign
//     | <assoc=right> NEG_OP expression   // logical
//     | expression (INT_MUL_OP | FLOAT_MUL_OP | INT_DIV_OP | FLOAT_DIV_OP | INT_REMAINDER_OP) expression // multiplying
//     | expression (INT_ADD_OP | FLOAT_ADD_OP | INT_SUB_OP | FLOAT_SUB_OP) expression // adding
//     | expression (CONJ_OP | DISJ_OP) expression // logical
//     | expression (EQ_OP | INT_NEQ_OP | FLOAT_NEQ_OP | INT_LT_OP | FLOAT_LT_OP | INT_GT_OP | FLOAT_GT_OP | INT_LTE_OP | FLOAT_LTE_OP | INT_GTE_OP | FLOAT_GTE_OP) expression // relational : assoc none ????
//     | (ID | INTLIT | FLOATLIT | STRINGLIT | BOOLEANLIT | arraylit) ; // operands

expression :
    exp1 (EQ_OP | INT_NEQ_OP | FLOAT_NEQ_OP | INT_LT_OP | FLOAT_LT_OP | INT_GT_OP | FLOAT_GT_OP | INT_LTE_OP | FLOAT_LTE_OP | INT_GTE_OP | FLOAT_GTE_OP) exp1   // relational
    | exp1;

exp1 : exp1 (CONJ_OP | DISJ_OP) exp2 // logical
    | exp2;

exp2 : exp2 (INT_ADD_OP | FLOAT_ADD_OP | INT_SUB_OP | FLOAT_SUB_OP) exp3 // adding
    | exp3;

exp3 : exp3 (INT_MUL_OP | FLOAT_MUL_OP | INT_DIV_OP | FLOAT_DIV_OP | INT_REMAINDER_OP) exp4 // multiplying
    | exp4;

exp4 : NEG_OP exp4   // logical
    | exp5;

exp5 : (INT_SUB_OP | FLOAT_SUB_OP) exp5  // sign
    | exp6;

exp6 : exp7 (LSB expression RSB)+   // index expression: (ID | func_call) or exp7 ???
    | exp7;

exp7 : LP expression RP
    | func_call // function call : assoc none ?????
    | (ID | literal) ; // operands

// exp6 : LP expression RP
//     | func_call // function call : assoc none ?????
//     | (ID | func_call) (LSB expression RSB)+ // ID or func_call | exp higher precedence  ???
//     | (ID | INTLIT | FLOATLIT | STRINGLIT | BOOLEANLIT | arraylit) ; // operands
    
// Identifiers
ID: [a-z][a-zA-Z0-9_]* ;

// Literals
// Integers
INTLIT : BASE10 | BASE16 | BASE8;
fragment BASE10 : '0' | [1-9][0-9]*;
fragment BASE8 : '0' [oO] [1-7][0-7]*;
fragment BASE16 : '0' [xX] [1-9A-F] [0-9A-F]*;
// Floats
fragment DIGIT : [0-9];
fragment INT_PART : DIGIT+;
fragment DECIMAL_PART : DOT DIGIT*;
fragment EXPONENT_PART : [eE] [+-]? DIGIT+;
FLOATLIT : INT_PART (DECIMAL_PART | EXPONENT_PART | DECIMAL_PART EXPONENT_PART);
// Boolean
BOOLEANLIT : 'True' | 'False';
// String   ??????????
STRINGLIT : '"' STR_CHAR* '"'
    {
        value = str(self.text);
        self.text = value[1:-1]
    }; 
fragment STR_CHAR : ('\\' ['bfrnt\\]) | ('\'' '"') | ~['"\n\\];

// Array
// arraylit : LCB WS* (LITERAL WS* (COMMA WS* LITERAL WS*)*)? RCB;  // remove white space when return token ???
arraylit : LCB (literal (COMMA literal)*)? RCB;  // remove white space when return token ???
literal : INTLIT | FLOATLIT | BOOLEANLIT | STRINGLIT | arraylit;

// Keywords
BODY : 'Body';
ELSE : 'Else';
END_FOR : 'EndFor';
IF : 'If';
VAR : 'Var';
END_DO : 'EndDo';
BREAK : 'Break';
ELSE_IF : 'ElseIf';
END_WHILE : 'EndWhile';
PARAMETER : 'Parameter';
WHILE : 'While';
CONTINUE : 'Continue';
END_BODY : 'EndBody';
FOR : 'For';
RETURN : 'Return';
OPERATORS : 'Operators';
DO : 'Do';
END_IF : 'EndIf';
FUNCTION: 'Function';
THEN : 'Then';

// Operators
// Arithmetic operators
INT_SUB_OP : '-';
FLOAT_SUB_OP : '-.';
INT_ADD_OP : '+';
FLOAT_ADD_OP : '+.';
INT_MUL_OP : '*';
FLOAT_MUL_OP : '*.';
INT_DIV_OP : '\\';
FLOAT_DIV_OP : '\\.';
INT_REMAINDER_OP : '%';
// Boolean operators
NEG_OP : '!';
CONJ_OP : '&&';
DISJ_OP : '||';
// Relational operators
EQ_OP : '==';
INT_NEQ_OP : '!=';
INT_LT_OP : '<';
INT_GT_OP : '>';
INT_LTE_OP : '<=';
INT_GTE_OP : '>=';
FLOAT_NEQ_OP : '=/=';
FLOAT_LT_OP : '<.';
FLOAT_GT_OP : '>.';
FLOAT_LTE_OP : '<=.';
FLOAT_GTE_OP : '>=.';
// Assignment operator
ASSIGN_OP : '=';

// Separators
LP : '(';
RP : ')';
LSB : '[';
RSB : ']';
LCB : '{';
RCB : '}';
COLON: ':' ;
SEMI: ';' ;
COMMA : ',';
DOT : '.';


COMMENT : '**' .*? '**' -> skip;    // ????
WS : [ \t\r\n]+ -> skip ; // skip spaces, tabs, newlines

// Errors
ERROR_CHAR: .;
UNCLOSE_STRING: '"' STR_CHAR*
    {
        value = str(self.text)
        self.text = value[1:]
    };
ILLEGAL_ESCAPE: '"' STR_CHAR* ('\\' ~['bfrnt\\] | '\'' .) // \n is illegal escape or unclose string. Note the last dot 
    {
        value = str(self.text)
        self.text = value[1:]
    };
UNTERMINATED_COMMENT: '**' .*?; // ?????
