import unittest
from TestUtils import TestChecker
from StaticError import *
from AST import *

class CheckSuite(unittest.TestCase):

    # Predefined test cases
    def test_undeclared_function(self):
        """Simple program: main"""
        input = """Function: main
                   Body: 
                        foo();
                   EndBody."""
        expect = str(Undeclared(Function(),"foo"))
        self.assertTrue(TestChecker.test(input,expect,400))

    def test_diff_numofparam_stmt(self):
        """Complex program"""
        input = """Function: main  
                   Body:
                        printStrLn();
                    EndBody."""
        expect = str(TypeMismatchInStatement(CallStmt(Id("printStrLn"),[])))
        self.assertTrue(TestChecker.test(input,expect,401))
    
    def test_diff_numofparam_expr(self):
        """More complex program"""
        input = """Function: main 
                    Body:
                        printStrLn(read(4));
                    EndBody."""
        expect = str(TypeMismatchInExpression(CallExpr(Id("read"),[IntLiteral(4)])))
        self.assertTrue(TestChecker.test(input,expect,402))

    def test_undeclared_function_use_ast(self):
        """Simple program: main """
        input = Program([FuncDecl(Id("main"),[],([],[
            CallExpr(Id("foo"),[])]))])
        expect = str(Undeclared(Function(),"foo"))
        self.assertTrue(TestChecker.test(input,expect,403))

    def test_diff_numofparam_expr_use_ast(self):
        """More complex program"""
        input = Program([
                FuncDecl(Id("main"),[],([],[
                    CallStmt(Id("printStrLn"),[
                        CallExpr(Id("read"),[IntLiteral(4)])
                        ])]))])
        expect = str(TypeMismatchInExpression(CallExpr(Id("read"),[IntLiteral(4)])))
        self.assertTrue(TestChecker.test(input,expect,404))

    def test_diff_numofparam_stmt_use_ast(self):
        """Complex program"""
        input = Program([
                FuncDecl(Id("main"),[],([],[
                    CallStmt(Id("printStrLn"),[])]))])
        expect = str(TypeMismatchInStatement(CallStmt(Id("printStrLn"),[])))
        self.assertTrue(TestChecker.test(input,expect,405))

    # Test entry point
    def test_no_entry_point_1(self):
        """Simple program: main"""
        input = """Var: x, y, z;"""
        expect = str(NoEntryPoint())
        self.assertTrue(TestChecker.test(input,expect,406))

    def test_no_entry_point_2(self):
        """Simple program: main"""
        input = """Var: x, main, z;"""
        expect = str(NoEntryPoint())
        self.assertTrue(TestChecker.test(input,expect,407))

    def test_no_entry_point_3(self):
        """Simple program: main"""
        input = """Var: x, main, z;
        Function: foo
            Body:
            EndBody."""
        expect = str(NoEntryPoint())
        self.assertTrue(TestChecker.test(input,expect,408))

    def test_valid_entry_point(self):
        """Simple program: main"""
        input = """Var: x, y, z;
        Function: main
            Body:
            EndBody."""
        expect = str("")
        self.assertTrue(TestChecker.test(input,expect,409))

    # Test redeclare variable
    def test_redeclare_variable_1(self):
        """Simple program: main"""
        input = """Var: x, x, z;
        Function: main
            Body:
            EndBody."""
        expect = str(Redeclared(Variable(), "x"))
        self.assertTrue(TestChecker.test(input,expect,410))    

    def test_redeclare_variable_2(self):
        """Simple program: main"""
        input = """Var: x, y = {1,2,3}, z;
        Var: m, n[2][3], y = 1;
        Function: main
            Body:
            EndBody."""
        expect = str(Redeclared(Variable(), "y"))
        self.assertTrue(TestChecker.test(input,expect,411)) 

    def test_redeclare_variable_3(self):
        """Simple program: main"""
        input = """
        Function: main
            Parameter: x, y[4], z
            Body:
                Var: y = {1,2,3}, m, n;
            EndBody."""
        expect = str(Redeclared(Variable(), "y"))
        self.assertTrue(TestChecker.test(input,expect,412)) 

    # Test valid var declare
    def test_valid_declare_variable(self):
        """Simple program: main"""
        input = """
        Var: x, y, z;
        Function: main
            Body:
                Var: x, y, z, main;
            EndBody."""
        expect = str("")
        self.assertTrue(TestChecker.test(input,expect,413)) 

    # Test redeclare parameter
    def test_redeclare_parameter(self):
        """Simple program: main"""
        input = """
        Function: main
            Parameter: x,x,y
            Body:
            EndBody."""
        expect = str(Redeclared(Parameter(), "x"))
        self.assertTrue(TestChecker.test(input,expect,414))    

    # Test valid param declare
    def test_valid_declare_parameter(self):
        """Simple program: main"""
        input = """Var: x, y, z;
        Function: main
            Parameter: x, y, z, main
            Body:
            EndBody."""
        expect = str("")
        self.assertTrue(TestChecker.test(input,expect,415))

    # Test redeclare function
    def test_redeclare_function_1(self):
        """Simple program: main"""
        input = """Var: x, main, y;
        Function: main
            Body:
            EndBody."""
        expect = str(Redeclared(Function(), "main"))
        self.assertTrue(TestChecker.test(input,expect,416))    

    def test_redeclare_function_2(self):
        """Simple program: main"""
        input = """
        Function: foo
            Body:
            EndBody.
        Function: main
            Body:
            EndBody.
        Function: foo
            Parameter: x,y,z
            Body:
            EndBody."""
        expect = str(Redeclared(Function(), "foo"))
        self.assertTrue(TestChecker.test(input,expect,417))   

    # Test undeclare identifier
    def test_undeclare_identifier_1(self):
        """Simple program: main"""
        input = """
        Function: main
            Body:
                x = 1;
            EndBody."""
        expect = str(Undeclared(Identifier(), "x"))
        self.assertTrue(TestChecker.test(input,expect,418))       

    def test_undeclare_identifier_2(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                x = y + 1;
            EndBody."""
        expect = str(Undeclared(Identifier(), "y"))
        self.assertTrue(TestChecker.test(input,expect,419)) 

    def test_undeclare_identifier_3(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: foo
            Parameter: x
            Body:
                x = 1.1;
                Return x;
            EndBody.        
        Function: main
            Body:
                y = foo(x) +. 2.2;
            EndBody."""
        expect = str(Undeclared(Identifier(), "y"))
        self.assertTrue(TestChecker.test(input,expect,420))

    def test_undeclare_identifier_4(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: foo
            Parameter: x
            Body:
                x = 1;
                Return x;
            EndBody.        
        Function: main
            Body:
                x = foo + 1;
                Return;
            EndBody."""
        expect = str(Undeclared(Identifier(), "foo"))
        self.assertTrue(TestChecker.test(input,expect,421))

    def test_undeclare_identifier_5(self):  # one error ???
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                Var: y;
                x = y()[1] + 1;
                Return;
            EndBody."""
        expect = str(Undeclared(Function(), "y"))
        self.assertTrue(TestChecker.test(input,expect,422))

    def test_undeclare_identifier_6(self):  # one error ???
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                Var: y;
                x()[1] = y + 1;
                Return;
            EndBody."""
        expect = str(Undeclared(Function(), "x"))
        self.assertTrue(TestChecker.test(input,expect,423))

    # Test undeclare function
    def test_undeclare_function_1(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                x = foo(1);
            EndBody."""
        expect = str(Undeclared(Function(), "foo"))
        self.assertTrue(TestChecker.test(input,expect,424)) 

    def test_undeclare_function_2(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                Var: foo;
                x = foo(1);
            EndBody."""
        expect = str(Undeclared(Function(), "foo"))
        self.assertTrue(TestChecker.test(input,expect,425)) 

    def test_undeclare_function_3(self):    # ???
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                Var: foo;
                x = 1 + 2 - foo(1);
            EndBody.
        Function: foo
            Parameter: x
            Body:
                Return x;
            EndBody."""
        expect = str(Undeclared(Function(), "foo"))
        self.assertTrue(TestChecker.test(input,expect,426)) 

    # Test unidentical array dimension
    def test_unidentical_array_dimension_1(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Parameter: x[2][3], y
            Body:
                x = {1,2,3};
                Return;
            EndBody."""
        expect = str(TypeMismatchInStatement(Assign(Id("x"), ArrayLiteral([IntLiteral(1),IntLiteral(2),IntLiteral(3)]))))
        self.assertTrue(TestChecker.test(input,expect,427))    

    def test_unidentical_array_dimension_2(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                Var: x[2][3];
                Var: y[3][2] = { {1,2}, {3,4}, {5,6} };
                x = y;
                Return;
            EndBody."""
        expect = str(TypeMismatchInStatement(Assign(Id("x"), Id("y"))))
        self.assertTrue(TestChecker.test(input,expect,428))    

    # Test identical array dimension
    def test_identical_array_dimension(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                Var: x[3][2] = { {6,5}, {4,3}, {2,1} };
                Var: y[3][2] = { {1,2}, {3,4}, {5,6} };
                x = y;
                Return;
            EndBody."""
        expect = str("")
        self.assertTrue(TestChecker.test(input,expect,429)) 

    # Test unidentical array element type
    def test_unidentical_array_eletype(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                Var: x[3][2] = { {6.6,5.5}, {4.4,3.3}, {2.2,1.1} };
                Var: y[3][2] = { {1,2}, {3,4}, {5,6} };
                x = y;
                Return;
            EndBody."""
        expect = str(TypeMismatchInStatement(Assign(Id("x"), Id("y"))))
        self.assertTrue(TestChecker.test(input,expect,430))

    # Test invalid array indexing
    def test_invalid_array_index_1(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                Var: x[3][2] = { {6.6,5.5}, {4.4,3.3}, {2.2,1.1} };
                x[2] = {1.1, 2.2};
                Return;
            EndBody."""
        expect = str(TypeMismatchInExpression(ArrayCell(Id("x"), [IntLiteral(2)])))
        self.assertTrue(TestChecker.test(input,expect,431))    

    def test_invalid_array_index_2(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                Var: x[3][2] = { {6.6,5.5}, {4.4,3.3}, {2.2,1.1} };
                Var: y = 5, z = 1.2;
                x[y + y*2 - 4 \\ 2 % 2][z +. z *. 2.2] = 1.1;
                Return;
            EndBody."""
        expect = str(TypeMismatchInExpression(ArrayCell(Id("x"),[BinaryOp("-",BinaryOp("+",Id("y"),BinaryOp("*",Id("y"),IntLiteral(2))),BinaryOp("%",BinaryOp("\\",IntLiteral(4),IntLiteral(2)),IntLiteral(2))),BinaryOp("+.",Id("z"),BinaryOp("*.",Id("z"),FloatLiteral(2.2)))])))
        self.assertTrue(TestChecker.test(input,expect,432))

    # Test invalid unary op
    def test_invalid_unary_op(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                Var: x, y = 1e3, z = 10;
                z = - z;
                x = !!x;
                y = -. -. -.y;
                x = !(-x);
                Return;
            EndBody."""
        expect = str(TypeMismatchInExpression(UnaryOp("-", Id("x"))))
        self.assertTrue(TestChecker.test(input,expect,433))            

    # Test invalid binary op
    def test_invalid_binary_op_1(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                Var: x,y,z;
                x = (1 + 2 *3 \\ 4 % 5) * 6;
                y = 1.1 *. 2.2 +. 3.3 -. 4.4 \\. 5.5;
                z = x + y;
                Return;
            EndBody."""
        expect = str(TypeMismatchInExpression(BinaryOp("+", Id("x"), Id("y"))))
        self.assertTrue(TestChecker.test(input,expect,434))        

    def test_invalid_binary_op_2(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                Var: x,y,z;
                Var: t;
                t = !x && y || !z;
                t = !x + 1;
                Return;
            EndBody."""
        expect = str(TypeMismatchInExpression(BinaryOp("+", UnaryOp("!", Id("x")), IntLiteral(1))))
        self.assertTrue(TestChecker.test(input,expect,435)) 

    def test_invalid_binary_op_3(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                Var: x,y,z;
                Var: t, m, n, k = True;
                t = x * y - z * (x \\ 2 + 1);
                k = (m =/= n) && ( m >=. n) || (m <. n);
                x = t >= z;
                Return;
            EndBody."""
        expect = str(TypeMismatchInStatement(Assign(Id("x"), BinaryOp(">=", Id("t"), Id("z")))))
        self.assertTrue(TestChecker.test(input,expect,436))

    # Test type cannot be inferred
    def test_type_cannot_be_inferred_1(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Parameter: x
            Body:
                Var: y;
                x = y;
                Return;
            EndBody."""
        expect = str(TypeCannotBeInferred(Assign(Id("x"), Id("y"))))
        self.assertTrue(TestChecker.test(input,expect,437))

    def test_type_cannot_be_inferred_2(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Parameter: x[2][3]
            Body:
                Var: y[2][3];
                x = y;
                Return;
            EndBody."""
        expect = str(TypeCannotBeInferred(Assign(Id("x"), Id("y"))))
        self.assertTrue(TestChecker.test(input,expect,438))

    def test_type_cannot_be_inferred_3(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Parameter: x
            Body:
                Var: y, a = 10;
                y = a + foo(x);
                Return;
            EndBody.
        Function: foo
            Parameter: x
            Body:
                Return 1;
            EndBody."""
        expect = str(TypeCannotBeInferred(Assign(Id("y"), BinaryOp("+", Id("a"), CallExpr(Id("foo"), [Id("x")])))))
        self.assertTrue(TestChecker.test(input,expect,439))

    def test_type_cannot_be_inferred_4(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Parameter: x
            Body:
                Var: y, a = True;
                y = !a && !foo(x);
                Return;
            EndBody.
        Function: foo
            Parameter: x
            Body:
                Return False;
            EndBody."""
        expect = str(TypeCannotBeInferred(Assign(Id("y"), BinaryOp("&&", UnaryOp("!",Id("a")), UnaryOp("!", CallExpr(Id("foo"), [Id("x")]))))))
        self.assertTrue(TestChecker.test(input,expect,440))

    def test_type_cannot_be_inferred_5(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Parameter: x
            Body:
                Var: y, a = True;
                y = !a && foo(x)[1];
                Return;
            EndBody.
        Function: foo
            Parameter: x
            Body:
                Return {True, False};
            EndBody."""
        expect = str(TypeCannotBeInferred(Assign(Id("y"), BinaryOp("&&", UnaryOp("!",Id("a")), ArrayCell(CallExpr(Id("foo"), [Id("x")]), [IntLiteral(1)])))))
        self.assertTrue(TestChecker.test(input,expect,441))

    def test_type_cannot_be_inferred_6(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                foo(x);
                Return;
            EndBody.
        Function: foo
            Parameter: x
            Body:
                Return;
            EndBody."""
        expect = str(TypeCannotBeInferred(CallStmt(Id("foo"), [Id("x")])))
        self.assertTrue(TestChecker.test(input,expect,442))

    # Test voidtype
    def test_voidtype_in_assign(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                foo(1);
                x = foo(1);
                Return;
            EndBody.
        Function: foo
            Parameter: x
            Body:
                Return;
            EndBody."""
        expect = str(TypeMismatchInStatement(Assign(Id("x"), CallExpr(Id("foo"), [IntLiteral(1)]))))
        self.assertTrue(TestChecker.test(input,expect,443))

    def test_voidtype_in_expression(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                foo(1);
                x = foo(1) + 2;
                Return;
            EndBody.
        Function: foo
            Parameter: x
            Body:
                Return;
            EndBody."""
        expect = str(TypeMismatchInExpression(BinaryOp("+", CallExpr(Id("foo"), [IntLiteral(1)]), IntLiteral(2))))
        self.assertTrue(TestChecker.test(input,expect,444))

    def test_voidtype_in_funccall(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                foo(1);
                foo(foo(10));
                Return;
            EndBody.
        Function: foo
            Parameter: x
            Body:
                Return;
            EndBody."""
        expect = str(TypeMismatchInStatement(CallStmt(Id("foo"), [CallExpr(Id("foo"), [IntLiteral(10)])])))
        self.assertTrue(TestChecker.test(input,expect,445))


    # Test return type
    def test_returntype_1(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                x = foo(10) +. 1.1;
            EndBody.
        Function: foo
            Parameter: x
            Body:
                Return 1;
            EndBody."""
        expect = str(TypeMismatchInStatement(Return(IntLiteral(1))))
        self.assertTrue(TestChecker.test(input,expect,446))

    def test_returntype_2(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: foo
            Parameter: x
            Body:
                Return 1;
            EndBody.
        Function: main
            Body:
                x = foo(10) +. 1.1;
            EndBody."""
        expect = str(TypeMismatchInExpression(BinaryOp("+.", CallExpr(Id("foo"), [IntLiteral(10)]), FloatLiteral(1.1))))
        self.assertTrue(TestChecker.test(input,expect,447))

    def test_returntype_3(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                foo(10);
            EndBody.
        Function: foo
            Parameter: x
            Body:
                Return 1;
            EndBody."""
        expect = str(TypeMismatchInStatement(Return(IntLiteral(1))))
        self.assertTrue(TestChecker.test(input,expect,448))

    def test_returntype_4(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: foo
            Parameter: x[3]
            Body:
                x = {4,5,6};
                Return;
            EndBody.
        Function: main
            Body:
                foo(goo());
            EndBody.
        Function: goo
            Body:
                Return {1,2,3,4};
            EndBody."""
        expect = str(TypeMismatchInStatement(Return(ArrayLiteral([IntLiteral(1),IntLiteral(2),IntLiteral(3),IntLiteral(4)]))))
        self.assertTrue(TestChecker.test(input,expect,449))

    def test_returntype_5(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: foo
            Parameter: x[3]
            Body:
                x = {4,5,6};
                Return 1;
            EndBody.
        Function: main
            Body:
                x = foo(goo()) + 1;
            EndBody.
        Function: goo
            Body:
                Return {1,2,3,4};
            EndBody."""
        expect = str(TypeMismatchInStatement(Return(ArrayLiteral([IntLiteral(1),IntLiteral(2),IntLiteral(3),IntLiteral(4)]))))
        self.assertTrue(TestChecker.test(input,expect,450))

    def test_returntype_6(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: foo
            Parameter: x[3]
            Body:
                While (True) Do
                    x = {4,5,6};
                    Return 1;
                EndWhile.
            EndBody.
        Function: main
            Body:
                x = foo(goo()) +. 1.1;
            EndBody.
        Function: goo
            Body:
                Return {1,2,3};
            EndBody."""
        expect = str(TypeMismatchInExpression(BinaryOp("+.", CallExpr(Id("foo"), [CallExpr(Id("goo"), [])]), FloatLiteral(1.1))))
        self.assertTrue(TestChecker.test(input,expect,451))

    def test_returntype_7(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: foo
            Parameter: x[3]
            Body:
                While (True) Do
                    x = {4,5,6};
                    Return 1;
                EndWhile.
            EndBody.
        Function: main
            Body:
                x = foo(goo()) + 1;
            EndBody.
        Function: goo
            Body:
                If (1 > 2) Then Return {1,2,3};
                Else Return {1.1, 2.2, 3.3};
                EndIf.
            EndBody."""
        expect = str(TypeMismatchInStatement(Return(ArrayLiteral([FloatLiteral(1.1), FloatLiteral(2.2), FloatLiteral(3.3)]))))
        self.assertTrue(TestChecker.test(input,expect,452))

    def test_returntype_8(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: foo
            Parameter: x[3]
            Body:
                Return;
            EndBody.
        Function: main
            Body:
                Return foo({1,2,3});
            EndBody."""
        expect = str(TypeMismatchInStatement(Return(CallExpr(Id("foo"), [ArrayLiteral([IntLiteral(1), IntLiteral(2), IntLiteral(3)])]))))
        self.assertTrue(TestChecker.test(input,expect,453))

    # Test assign
    def test_assign_1(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                x = x + foo(x);
            EndBody.
        Function: foo
            Parameter: x
            Body:
                Return 1;
            EndBody."""
        expect = str("")
        self.assertTrue(TestChecker.test(input,expect,454))

    def test_assign_2(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                x = foo(x) + x;
            EndBody.
        Function: foo
            Parameter: x
            Body:
                Return 1;
            EndBody."""
        expect = str(TypeCannotBeInferred(Assign(Id("x"), BinaryOp("+", CallExpr(Id("foo"), [Id("x")]), Id("x")))))
        self.assertTrue(TestChecker.test(input,expect,455))

    def test_assign_3(self):
        """Simple program: main"""
        input = """
        Function: main
            Body:
                Var: x, y[5] = {1,2,3,4,5};
                x = y;
            EndBody."""
        expect = str(TypeMismatchInStatement(Assign(Id("x"), Id("y"))))
        self.assertTrue(TestChecker.test(input,expect,456))

    def test_assign_4(self):
        """Simple program: main"""
        input = """
        Function: main
            Body:
                Var: x[3], y[5] = {1,2,3,4,5};
                x = y;
            EndBody."""
        expect = str(TypeMismatchInStatement(Assign(Id("x"), Id("y"))))
        self.assertTrue(TestChecker.test(input,expect,457))

    def test_assign_5(self):
        """Simple program: main"""
        input = """
        Function: main
            Body:
                Var: x[5] = {1.1, 2.2, 3.3, 4.4, 5.5}, y[5] = {1,2,3,4,5};
                y = foo(1);
                foo(2)[0] = x[3];
                Return;
            EndBody.
        Function: foo
            Parameter: x
            Body:
                Return {5,4,3,2,1};
            EndBody.
            """
        expect = str(TypeMismatchInStatement(Assign(ArrayCell(CallExpr(Id("foo"), [IntLiteral(2)]), [IntLiteral(0)]), ArrayCell(Id("x"), [IntLiteral(3)]))))
        self.assertTrue(TestChecker.test(input,expect,458))

    def test_assign_6(self):
        """Simple program: main"""
        input = """
        Var: x[5];
        Function: main
            Body:
                Var: y[5] = {1,2,3,4,5};
                x = {1.1, 2.2, 3.3, 4.4, 5.5};
                y = foo(1);
                foo(y[4] + 2)[0] = y[0] + 1;
                Return;
            EndBody.
        Function: foo
            Parameter: y
            Body:
                y = x[1];
                Return {5,4,3,2,1};
            EndBody.
            """
        expect = str(TypeMismatchInStatement(Assign(Id("y"), ArrayCell(Id("x"), [IntLiteral(1)]))))
        self.assertTrue(TestChecker.test(input,expect,459))

    def test_assign_7(self):
        """Simple program: main"""
        input = """
        Function: goo
            Parameter: x
            Body:
                Return True;
            EndBody.
        Function: main
            Body:
                Var: a, b;
                b = goo(a < b);
                Return;
            EndBody."""
        expect = str(TypeMismatchInStatement(Assign(Id("b"), CallExpr(Id("goo"), [BinaryOp("<", Id("a"), Id("b"))]))))
        self.assertTrue(TestChecker.test(input,expect,460))

    def test_assign_8(self):
        """Simple program: main"""
        input = """
        Function: foo
            Parameter: x
            Body:
                Return {True,False};
            EndBody.
        Function: main
            Body:
                Var: a,b;
                foo(True)[0] = foo(1)[1];
                Return;
            EndBody."""
        expect = str(TypeMismatchInExpression(CallExpr(Id("foo"), [IntLiteral(1)])))
        self.assertTrue(TestChecker.test(input,expect,461))

    # Test function call
    def test_function_call_1(self):
        """Simple program: main"""
        input = """
        Var: x[2][2] = {{1.1, 2.2},{3.3, 4.4}};
        Function: main
            Body:
                x = foo(x);
                Return;
            EndBody.
        Function: foo
            Parameter: y[2][2]
            Body:
                Return {{1,2},{3,4}};
            EndBody.
            """
        expect = str(TypeMismatchInStatement(Return(ArrayLiteral([ArrayLiteral([IntLiteral(1),IntLiteral(2)]),ArrayLiteral([IntLiteral(3),IntLiteral(4)])]))))
        self.assertTrue(TestChecker.test(input,expect,462))

    def test_function_call_2(self):
        """Simple program: main"""
        input = """
        Function: main
            Parameter: x, y, z[2]
            Body:
                While (x > int_of_float(z[x])) Do
                    y = z[1];
                    main(1, 1.1, {1,2});
                EndWhile.
                Return;
            EndBody.
            """
        expect = str(TypeMismatchInStatement(CallStmt(Id("main"), [IntLiteral(1), FloatLiteral(1.1), ArrayLiteral([IntLiteral(1), IntLiteral(2)])])))
        self.assertTrue(TestChecker.test(input,expect,463))

    def test_function_call_3(self):
        """Simple program: main"""
        input = """
        Var: t[2];
        Function: foo
            Parameter: x, y, z[2]
            Body:
                While (x > int_of_float(z[x])) Do
                    y = z[1];
                    x = foo(1, 1.1, t);
                EndWhile.
                Return 1;
            EndBody.
        Function: main
            Body:
                t = {1,2};
                Return;
            EndBody."""
        expect = str(TypeMismatchInStatement(Assign(Id("t"), ArrayLiteral([IntLiteral(1), IntLiteral(2)]))))
        self.assertTrue(TestChecker.test(input,expect,464))

    def test_function_call_4(self):
        """Simple program: main"""
        input = """
        Var: t[2];
        Function: foo
            Parameter: x, y, z[2]
            Body:
                While (x > int_of_float(z[x])) Do
                    y = z[1];
                    x = foo(1, 1.1, t);
                EndWhile.
                Return 1;
            EndBody.
        Function: main
            Body:
                t = {1.1,2.2};
                foo(1, 1.1, t);
                Return;
            EndBody."""
        expect = str(TypeMismatchInStatement(CallStmt(Id("foo"), [IntLiteral(1), FloatLiteral(1.1), Id("t")])))
        self.assertTrue(TestChecker.test(input,expect,465))

    def test_function_call_5(self):
        """Simple program: main"""
        input = """
        Function: main
            Body:
                Var: x;
                x = foo(foo(1) > 1);
                Return;
            EndBody.
        Function: foo
            Parameter: x
            Body:
                Return 1;
            EndBody."""
        expect = str(TypeMismatchInExpression(CallExpr(Id("foo"), [BinaryOp(">", CallExpr(Id("foo"), [IntLiteral(1)]), IntLiteral(1))])))
        self.assertTrue(TestChecker.test(input,expect,466))

    def test_function_call_6(self):
        """Simple program: main"""
        input = """
        Function: main
            Body:
                Var: x;
                x = foo(1, foo(1.1, 1));
                Return;
            EndBody.
        Function: foo
            Parameter: x, y
            Body:
                Return 1;
            EndBody."""
        expect = str(TypeMismatchInExpression(CallExpr(Id("foo"), [FloatLiteral(1.1), IntLiteral(1)])))
        self.assertTrue(TestChecker.test(input,expect,467))

    def test_function_call_7(self):
        """Simple program: main"""
        input = """
        Function: foo
            Parameter: x
            Body:
                x = 1;
                Return {0};
            EndBody.
        Function: main
            Body:
                foo(goo(1)[0])[0] = foo(1)[1];
                Return;
            EndBody.
        Function: goo
            Parameter: x
            Body:
                Return {0};
            EndBody."""
        expect = str(TypeCannotBeInferred(Assign(    ArrayCell(CallExpr(Id("foo"), [ArrayCell(CallExpr(Id("goo"), [IntLiteral(1)]), [IntLiteral(0)])]), [IntLiteral(0)]),      ArrayCell(CallExpr(Id("foo"), [IntLiteral(1)]), [IntLiteral(1)])     )))
        self.assertTrue(TestChecker.test(input,expect,468))

    def test_function_call_8(self):
        """Simple program: main"""
        input = """
        Function: foo
            Parameter: x
            Body:
                x = 1;
                Return;
            EndBody.
        Function: main
            Body:
                Var: x;
                foo(goo(x));
                Return;
            EndBody.
        Function: goo
            Parameter: x
            Body:
                Return 1;
            EndBody."""
        expect = str(TypeCannotBeInferred(CallStmt(Id("foo"), [CallExpr(Id("goo"), [Id("x")])])))
        self.assertTrue(TestChecker.test(input,expect,469))

    # def test_function_call_8(self):
    #     """Simple program: main"""
    #     input = """
    #     Function: foo
    #         Parameter: x
    #         Body:
    #             Return {0};
    #         EndBody.
    #     Function: main
    #     Body:
    #         foo(goo(1)[0])[0] = goo(foo(1)[0])[0];
    #         Return;
    #     EndBody.
    #     Function: goo
    #         Parameter: x
    #         Body:
    #             Return {0};
    #         EndBody."""
    #     expect = str(TypeMismatchInExpression(CallExpr(Id("foo"), [FloatLiteral(1.1), IntLiteral(1)])))
    #     self.assertTrue(TestChecker.test(input,expect,469))

    # Test while, do while
    def test_if_1(self):
        """Simple program: main"""
        input = """
        Function: main
            Body:
                Var: x;
                If (x > 1) Then Return 1;
                ElseIf (x < 1) Then
                    Var: y;
                    y = x + 1;
                    Return 2;
                Else
                    y = x - 1;
                    Return 3;
                EndIf.
            EndBody."""
        expect = str(Undeclared(Identifier(), "y"))
        self.assertTrue(TestChecker.test(input,expect,470))

    def test_if_2(self):
        """Simple program: main"""
        input = """
        Function: main
            Body:
                Var: x;
                If (foo(x)) Then
                EndIf.
                Return;
            EndBody.
        Function: foo
            Parameter: x
            Body:
                Return True;
            EndBody."""
        expect = str(TypeCannotBeInferred(If([(CallExpr(Id("foo"), [Id("x")]), [], [])], ([],[]))))
        self.assertTrue(TestChecker.test(input,expect,471))

    def test_if_3(self):
        """Simple program: main"""
        input = """
        Var: x;
        Function: main
            Body:
                If (foo(1.1)) Then
                    x = 1;
                EndIf.
                Return;
            EndBody.
        Function: foo
            Parameter: y
            Body:
                y = x;
                Return True;
            EndBody."""
        expect = str(TypeMismatchInStatement(Assign(Id("y"), Id("x"))))
        self.assertTrue(TestChecker.test(input,expect,472))

    # def test_if_4(self):
    #     """Simple program: main"""
    #     input = """
    #     Function: foo
    #         Parameter: x, y
    #         Body:
    #             Return False;
    #         EndBody.
    #     Function: main
    #         Parameter: x,y,z
    #         Body:
    #             If (True) Then
    #                 main(1, 2.2, foo(x, y));
    #             EndIf.
    #             main(2, 1.1, "Hello");
    #             Return;
    #         EndBody."""
    #     expect = str(TypeMismatchInStatement(CallStmt(Id("main"), [Id("a"), Id("b"), StringLiteral("Hello")])))
    #     self.assertTrue(TestChecker.test(input,expect,473))










    # # Test not in loop
    # def test_not_in_loop_1(self):
    #     """Simple program: main"""
    #     input = """
    #     Var: x;
    #     Function: main
    #         Body:
    #             Break;
    #             Return;
    #         EndBody."""
    #     expect = str(NotInLoop(Break()))
    #     self.assertTrue(TestChecker.test(input,expect,500))

    # def test_not_in_loop_2(self):
    #     """Simple program: main"""
    #     input = """
    #     Var: x;
    #     Function: main
    #         Body:
    #             Continue;
    #             Return;
    #         EndBody."""
    #     expect = str(NotInLoop(Continue()))
    #     self.assertTrue(TestChecker.test(input,expect,501))

    # def test_not_in_loop_3(self):
    #     """Simple program: main"""
    #     input = """
    #     Var: x;
    #     Function: main
    #         Body:
    #             If (True) Then Var: x;
    #             ElseIf (False) Then Break;
    #             EndIf.
    #             Return;
    #         EndBody."""
    #     expect = str(NotInLoop(Break()))
    #     self.assertTrue(TestChecker.test(input,expect,502))

    # def test_not_in_loop_4(self):
    #     """Simple program: main"""
    #     input = """
    #     Var: x;
    #     Function: main
    #         Body:
    #             If (True) Then Var: x;
    #             ElseIf (False) Then Continue;
    #             EndIf.
    #             Return;
    #         EndBody."""
    #     expect = str(NotInLoop(Continue()))
    #     self.assertTrue(TestChecker.test(input,expect,503))

    # def test_not_in_loop_5(self):
    #     """Simple program: main"""
    #     input = """
    #     Var: x;
    #     Function: main
    #         Body:
    #             If (True) Then Var: x;
    #             ElseIf (False) Then
    #             Else
    #                 Var: y;
    #                 Break;
    #             EndIf.
    #             Return;
    #         EndBody."""
    #     expect = str(NotInLoop(Break()))
    #     self.assertTrue(TestChecker.test(input,expect,504))

    # def test_not_in_loop_6(self):
    #     """Simple program: main"""
    #     input = """
    #     Var: x;
    #     Function: main
    #         Body:
    #             If (True) Then Var: x;
    #             ElseIf (False) Then
    #             Else
    #                 Var: y;
    #                 Continue;
    #             EndIf.
    #             Return;
    #         EndBody."""
    #     expect = str(NotInLoop(Continue()))
    #     self.assertTrue(TestChecker.test(input,expect,505))

    # def test_not_in_loop_7(self):
    #     """Simple program: main"""
    #     input = """
    #     Var: x;
    #     Function: main
    #         Body:
    #             If (True) Then
    #                 If (True) Then Break;
    #                 EndIf.
    #             EndIf.
    #             Return;
    #         EndBody."""
    #     expect = str(NotInLoop(Break()))
    #     self.assertTrue(TestChecker.test(input,expect,506))

    # def test_not_in_loop_8(self):
    #     """Simple program: main"""
    #     input = """
    #     Var: x;
    #     Function: main
    #         Body:
    #             If (True) Then
    #                 If (True) Then Continue;
    #                 EndIf.
    #             EndIf.
    #             Return;
    #         EndBody."""
    #     expect = str(NotInLoop(Continue()))
    #     self.assertTrue(TestChecker.test(input,expect,507))

    # def test_not_in_loop_9(self):
    #     """Simple program: main"""
    #     input = """
    #     Var: x;
    #     Function: main
    #         Body:
    #             If (True) Then
    #                 If (True) Then
    #                 Else Break;
    #                 EndIf.
    #             EndIf.
    #             Return;
    #         EndBody."""
    #     expect = str(NotInLoop(Break()))
    #     self.assertTrue(TestChecker.test(input,expect,508))

    # def test_not_in_loop_10(self):
    #     """Simple program: main"""
    #     input = """
    #     Var: x;
    #     Function: main
    #         Body:
    #             If (True) Then
    #                 If (True) Then
    #                 Else Continue;
    #                 EndIf.
    #             EndIf.
    #             Return;
    #         EndBody."""
    #     expect = str(NotInLoop(Continue()))
    #     self.assertTrue(TestChecker.test(input,expect,509))

    # def test_not_in_loop_11(self):
    #     """Simple program: main"""
    #     input = """
    #     Var: x;
    #     Function: main
    #         Body:
    #             While (True) Do
    #                 If (True) Then
    #                     If (True) Then Break;
    #                     Else Break;
    #                     EndIf.
    #                     Break;
    #                 Else Break;
    #                 EndIf.
    #             EndWhile.
    #             Return;
    #         EndBody."""
    #     expect = str("")
    #     self.assertTrue(TestChecker.test(input,expect,510))

    # def test_not_in_loop_12(self):
    #     """Simple program: main"""
    #     input = """
    #     Var: x;
    #     Function: main
    #         Body:
    #             While (True) Do
    #                 If (True) Then
    #                     If (True) Then Continue;
    #                     Else Continue;
    #                     EndIf.
    #                     Continue;
    #                 Else Continue;
    #                 EndIf.
    #             EndWhile.
    #             Return;
    #         EndBody."""
    #     expect = str("")
    #     self.assertTrue(TestChecker.test(input,expect,511))

