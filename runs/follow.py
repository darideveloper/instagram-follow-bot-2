# Import modules from parent folder
import os
import sys
parent_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(parent_folder)

from bot import Bot

try:
    bot_instance = Bot()
    bot_instance.auto_follow ()
except Exception as err:   
    exception_type, exception_object, exception_traceback = sys.exc_info()
    filename = exception_traceback.tb_frame.f_code.co_filename
    line_number = exception_traceback.tb_lineno

    print (f"\n\tERROR: {err}")
    print("Exception type: ", exception_type)
    print("File name: ", filename)
    print("Line number: ", line_number)
    
    input ("Press Enter to exit...")