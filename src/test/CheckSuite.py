import unittest
from TestUtils import TestChecker
from StaticError import *
from AST import *

class CheckSuite(unittest.TestCase):

    # # Predefined test cases
    # def test_undeclared_function(self):
    #     """Simple program: main"""
    #     input = """Function: main
    #                Body: 
    #                     foo();
    #                EndBody."""
    #     expect = str(Undeclared(Function(),"foo"))
    #     self.assertTrue(TestChecker.test(input,expect,400))

    # def test_diff_numofparam_stmt(self):
    #     """Complex program"""
    #     input = """Function: main  
    #                Body:
    #                     printStrLn();
    #                 EndBody."""
    #     expect = str(TypeMismatchInStatement(CallStmt(Id("printStrLn"),[])))
    #     self.assertTrue(TestChecker.test(input,expect,401))
    
    # def test_diff_numofparam_expr(self):
    #     """More complex program"""
    #     input = """Function: main 
    #                 Body:
    #                     printStrLn(read(4));
    #                 EndBody."""
    #     expect = str(TypeMismatchInExpression(CallExpr(Id("read"),[IntLiteral(4)])))
    #     self.assertTrue(TestChecker.test(input,expect,402))

    # def test_undeclared_function_use_ast(self):
    #     """Simple program: main """
    #     input = Program([FuncDecl(Id("main"),[],([],[
    #         CallExpr(Id("foo"),[])]))])
    #     expect = str(Undeclared(Function(),"foo"))
    #     self.assertTrue(TestChecker.test(input,expect,403))

    # def test_diff_numofparam_expr_use_ast(self):
    #     """More complex program"""
    #     input = Program([
    #             FuncDecl(Id("main"),[],([],[
    #                 CallStmt(Id("printStrLn"),[
    #                     CallExpr(Id("read"),[IntLiteral(4)])
    #                     ])]))])
    #     expect = str(TypeMismatchInExpression(CallExpr(Id("read"),[IntLiteral(4)])))
    #     self.assertTrue(TestChecker.test(input,expect,404))

    # def test_diff_numofparam_stmt_use_ast(self):
    #     """Complex program"""
    #     input = Program([
    #             FuncDecl(Id("main"),[],([],[
    #                 CallStmt(Id("printStrLn"),[])]))])
    #     expect = str(TypeMismatchInStatement(CallStmt(Id("printStrLn"),[])))
    #     self.assertTrue(TestChecker.test(input,expect,405))

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
                y = foo(x) + 1;
            EndBody."""
        expect = str(Undeclared(Identifier(), "y"))
        self.assertTrue(TestChecker.test(input,expect,420))

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
        self.assertTrue(TestChecker.test(input,expect,421)) 

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
        self.assertTrue(TestChecker.test(input,expect,422)) 

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
        self.assertTrue(TestChecker.test(input,expect,423)) 

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
        self.assertTrue(TestChecker.test(input,expect,424))    

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
        self.assertTrue(TestChecker.test(input,expect,425))    

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
        self.assertTrue(TestChecker.test(input,expect,426)) 

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
        self.assertTrue(TestChecker.test(input,expect,427))

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
        self.assertTrue(TestChecker.test(input,expect,428))    

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
        self.assertTrue(TestChecker.test(input,expect,429))

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
        self.assertTrue(TestChecker.test(input,expect,430))            

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
        self.assertTrue(TestChecker.test(input,expect,431))        

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
        self.assertTrue(TestChecker.test(input,expect,432)) 

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
        self.assertTrue(TestChecker.test(input,expect,433))

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
        self.assertTrue(TestChecker.test(input,expect,434))

    def test_type_cannot_be_inferred_2(self):
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
        self.assertTrue(TestChecker.test(input,expect,435))

    def test_type_cannot_be_inferred_3(self):
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
        self.assertTrue(TestChecker.test(input,expect,436))

    def test_type_cannot_be_inferred_4(self):
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
        self.assertTrue(TestChecker.test(input,expect,437))