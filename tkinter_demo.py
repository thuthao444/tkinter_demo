#!/usr/bin/env python3
"""
Tkinter Demo Application - Calculator with Todo List
This application demonstrates common GUI programming patterns and contains several bugs.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import math
import json

class Calculator:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # BUG 1: Division by zero not handled properly
        self.display_var = tk.StringVar()
        self.display_var.set("0")
        
        # Display
        display = ttk.Entry(self.frame, textvariable=self.display_var, 
                          font=('Arial', 14), justify='right', state='readonly')
        display.grid(row=0, column=0, columnspan=4, sticky='ew', pady=5)
        
        # Buttons
        buttons = [
            ('C', 1, 0), ('±', 1, 1), ('%', 1, 2), ('÷', 1, 3),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2), ('×', 2, 3),
            ('4', 3, 0), ('5', 3, 1), ('6', 3, 2), ('-', 3, 3),
            ('1', 4, 0), ('2', 4, 1), ('3', 4, 2), ('+', 4, 3),
            ('0', 5, 0), ('.', 5, 1), ('=', 5, 2), ('√', 5, 3)
        ]
        
        for (text, row, col) in buttons:
            btn = ttk.Button(self.frame, text=text, 
                           command=lambda t=text: self.button_click(t))
            if text == '0':
                btn.grid(row=row, column=col, columnspan=2, sticky='ew', padx=1, pady=1)
            else:
                btn.grid(row=row, column=col, sticky='ew', padx=1, pady=1)
        
        # Configure grid weights
        for i in range(4):
            self.frame.columnconfigure(i, weight=1)
        
        self.reset()
    
    def reset(self):
        self.current = "0"
        self.operator = None
        self.operand = None
        self.display_var.set(self.current)
    
    def button_click(self, char):
        if char.isdigit() or char == '.':
            if self.current == "0" and char != '.':
                self.current = char
            else:
                self.current += char
        elif char in ['+', '-', '×', '÷']:
            if self.operand is not None and self.operator is not None:
                self.calculate()
            self.operand = float(self.current)
            self.operator = char
            self.current = "0"
        elif char == '=':
            self.calculate()
        elif char == 'C':
            self.reset()
        elif char == '±':
            if self.current != "0":
                if self.current.startswith('-'):
                    self.current = self.current[1:]
                else:
                    self.current = '-' + self.current
        elif char == '%':
            self.current = str(float(self.current) / 100)
        elif char == '√':
            # Fixed: Validate input for square root
            value = float(self.current)
            if value < 0:
                messagebox.showerror("Error", "Cannot compute square root of negative number!")
                return
            self.current = str(math.sqrt(value))
        
        self.display_var.set(self.current)
    
    def calculate(self):
        if self.operator and self.operand is not None:
            second_operand = float(self.current)
            
            if self.operator == '+':
                result = self.operand + second_operand
            elif self.operator == '-':
                result = self.operand - second_operand
            elif self.operator == '×':
                result = self.operand * second_operand
            elif self.operator == '÷':
                # Fixed: Handle division by zero
                if second_operand == 0:
                    messagebox.showerror("Error", "Cannot divide by zero!")
                    self.reset()
                    return
                result = self.operand / second_operand
            
            self.current = str(result)
            self.operand = None
            self.operator = None


class TodoList:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # BUG 3: Security vulnerability - eval() usage
        self.todos = []
        
        # Title
        title = ttk.Label(self.frame, text="Todo List", font=('Arial', 12, 'bold'))
        title.pack(pady=5)
        
        # Input frame
        input_frame = ttk.Frame(self.frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.todo_var = tk.StringVar()
        self.todo_entry = ttk.Entry(input_frame, textvariable=self.todo_var)
        self.todo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.todo_entry.bind('<Return>', lambda e: self.add_todo())
        
        add_btn = ttk.Button(input_frame, text="Add", command=self.add_todo)
        add_btn.pack(side=tk.RIGHT)
        
        # List frame
        list_frame = ttk.Frame(self.frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Listbox with scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        # Buttons frame
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        delete_btn = ttk.Button(btn_frame, text="Delete", command=self.delete_todo)
        delete_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        clear_btn = ttk.Button(btn_frame, text="Clear All", command=self.clear_todos)
        clear_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Fixed: Safe math calculator functionality
        eval_btn = ttk.Button(btn_frame, text="Math Calculator", command=self.execute_command)
        eval_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        save_btn = ttk.Button(btn_frame, text="Save", command=self.save_todos)
        save_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        load_btn = ttk.Button(btn_frame, text="Load", command=self.load_todos)
        load_btn.pack(side=tk.RIGHT)
        
    def add_todo(self):
        todo = self.todo_var.get().strip()
        if todo:
            self.todos.append(todo)
            self.listbox.insert(tk.END, todo)
            self.todo_var.set("")
    
    def delete_todo(self):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            self.listbox.delete(index)
            del self.todos[index]
    
    def clear_todos(self):
        self.listbox.delete(0, tk.END)
        self.todos.clear()
    
    def execute_command(self):
        # Fixed: Safe calculator instead of dangerous eval()
        command = self.todo_var.get().strip()
        if command:
            try:
                # Only allow basic mathematical expressions
                allowed_chars = set('0123456789+-*/()., ')
                if not all(c in allowed_chars for c in command):
                    messagebox.showerror("Error", "Only basic math operations are allowed (+, -, *, /, parentheses, numbers)")
                    return
                
                # Use ast.literal_eval for safer evaluation of mathematical expressions
                import ast
                import operator
                
                # Parse and evaluate mathematical expressions safely
                node = ast.parse(command, mode='eval')
                result = self._evaluate_math_expr(node.body)
                messagebox.showinfo("Result", f"Math result: {result}")
            except Exception as e:
                messagebox.showerror("Error", f"Invalid math expression: {str(e)}")
    
    def _evaluate_math_expr(self, node):
        """Safely evaluate mathematical expressions using AST"""
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._evaluate_math_expr(node.left)
            right = self._evaluate_math_expr(node.right)
            ops = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
            }
            if type(node.op) not in ops:
                raise ValueError(f"Unsupported operation: {type(node.op).__name__}")
            if isinstance(node.op, ast.Div) and right == 0:
                raise ValueError("Division by zero")
            return ops[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._evaluate_math_expr(node.operand)
            if isinstance(node.op, ast.USub):
                return -operand
            elif isinstance(node.op, ast.UAdd):
                return +operand
            else:
                raise ValueError(f"Unsupported unary operation: {type(node.op).__name__}")
        else:
            raise ValueError(f"Unsupported node type: {type(node).__name__}")
    
    def save_todos(self):
        try:
            with open('todos.json', 'w') as f:
                json.dump(self.todos, f)
            messagebox.showinfo("Success", "Todos saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
    
    def load_todos(self):
        try:
            with open('todos.json', 'r') as f:
                self.todos = json.load(f)
            self.listbox.delete(0, tk.END)
            for todo in self.todos:
                self.listbox.insert(tk.END, todo)
            messagebox.showinfo("Success", "Todos loaded successfully!")
        except FileNotFoundError:
            messagebox.showwarning("Warning", "No saved todos found.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load: {str(e)}")


class MainApplication:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Tkinter Demo - Calculator & Todo")
        self.root.geometry("600x500")
        self.root.minsize(400, 300)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Calculator tab
        calc_frame = ttk.Frame(notebook)
        notebook.add(calc_frame, text="Calculator")
        self.calculator = Calculator(calc_frame)
        
        # Todo tab
        todo_frame = ttk.Frame(notebook)
        notebook.add(todo_frame, text="Todo List")
        self.todo_list = TodoList(todo_frame)
    
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = MainApplication()
    app.run()