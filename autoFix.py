import os
import openai
import json
import subprocess
import datetime
import sys

# Define OpenAI API key
openai.api_key=os.getenv("OPENAI_API_KEY")
# Http error message form Zabbix 
data = sys.argv[1]

# Function definition to get config and parameter that is the errro cause
get_configfile_path_parameter_tools = [
    {
        "type": "function",
        "function":{
            "name":"get_file_info",
            "description":f"Assuming an environment using redhat, obtain the config file to be investigated, the path of the config file, and the parameters in the config file to be investigated from the httpd error log.",
            "parameters" :{
                "type": "object",
                "properties":{
                    "file":{
                        "type":"string",
                        "description":"the config file to be investigated."
                    },
                    "path":{
                        "type":"string",
                        "description":"The config file path to be investigated."
                    },
                    "parameter":{
                        "type":"string",
                        "description":"The paramter to be investigated."
                    }
                },
            "required":["file","path","parameter"]
            }
        },
        
    }
]

# Function definition to get value for parameter
get_value_tools = [
    {
        "type": "function",
        "function":{
            "name":"get_value_info",
            "description":f"Assumeing enviroment where redhat is used, value for parameters for resolving problems in httpd error logs are obtained from the configraton file and parameters.",
            "parameters" :{
                "type": "object",
                "properties":{
                    "before":{
                        "type":"string",
                        "description":"Value before fix"
                    },
                    "after":{
                        "type":"string",
                        "description":"Value after fix"
                    }
                },
            "required":["before","after"]
            }
        },
        
    },
]

try:
    # Response the config file,path and parameter
    response = openai.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role":"user","content":f"From the following log , answer the configuration file to be investigated,the path of configuration file to be investigated and the parameters within the configuration file to be investigated. Loggile:{data}"}
        ],
        tools=get_configfile_path_parameter_tools,
        tool_choice="auto",
        temperature=0
    )

    tool_calls=response.choices[0].message.tool_calls
    # If you called "function calling", run the bellow
    if(tool_calls):
        for tool_call in tool_calls:
            parameter=json.loads(tool_call.function.arguments)["parameter"]
            filepath = json.loads(tool_call.function.arguments)["path"]+json.loads(tool_call.function.arguments)["file"]
            # Run "cat [filepath]" to get file contents
            result = subprocess.run(f"cat {filepath}",shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            # If you get file contents, call "get_value_tools"
            if (result.returncode == 0):
                # Response value for fix 
                value_response = openai.chat.completions.create(
                    model="gpt-4-1106-preview",
                    messages=[
                        {"role":"assistant","content":f"Error log is occured due to the contents of configuration file of {filepath}.This contents of configuration file is the follow.\n\n{result.stdout}"},
                        {"role":"user","content":f"I would like to change the value of {parameter} in {filepath} to fix the following error log. Please tell me the value before fix and the value afiter fix."}
                    ],
                    tools=get_value_tools,
                    tool_choice="auto",
                    temperature=0
                )
                value_tool_calls=value_response.choices[0].message.tool_calls
                if(value_tool_calls):
                    beforeValue=json.loads(value_tool_calls[0].function.arguments)["before"]
                    afterValue=json.loads(value_tool_calls[0].function.arguments)["after"]
                    dt_now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')                
                    copyCommandResult=subprocess.run(f"cp -p {filepath} {filepath}_{dt_now}",shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    #If successed run that copy command, replace value
                    if(copyCommandResult.returncode==0):
                        changeCommand=f"sed -i s/\"{beforeValue}\"/\"{afterValue}\"/ {filepath}_{dt_now}"
                        commandRedult=subprocess.run(f"{changeCommand}",shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                        # If successed run that replace command, return value
                        if(commandRedult.returncode==0):
                            print(f"replace {afterValue} from {beforeValue} in {filepath}_{dt_now}")
                    else:
                            print(copyCommandResult.stderr)
                else:
                    print("Did not call value_tool_calls ")
            else:
                print("file not exited")
    else:
        print("Did not call get_configfile_path_parameter_tools")
except Exception as e:
    print(e)