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

    def test_undeclare_function_3(self):
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

    # # Test array cell
    # def test_undeclare_function_3(self):
    #     """Simple program: main"""
    #     input = """
    #     Var: x;
    #     Function: main
    #         Body:
    #             Var: foo;
    #             x = 1 + 2 - foo(1);
    #         EndBody.
    #     Function: foo
    #         Parameter: x
    #         Body:
    #             Return x;
    #         EndBody."""
    #     expect = str(Undeclared(Function(), "foo"))
    #     self.assertTrue(TestChecker.test(input,expect,423))    