import argparse
import logging
import os
from typing import Literal
import yaml  # 添加yaml库导入

from mysql.connector import connect, Error
from mcp.server import  FastMCP
from mcp.types import TextContent
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from sqlalchemy import text

from utils.db_config import DBConfig
from database_env import DataBaseEnv
from utils.db_source import HITLSQLDatabase
from utils.db_util import init_db_conn
from utils.file_util import extract_sql_from_qwen
from utils.llm_util import call_openai_sdk




# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("xiyan_mcp_server")


def get_yml_config():
    config_path = os.getenv("YML", os.path.join(os.path.dirname(__file__), "config_demo.yml"))
    logger.info(f"Loading configuration from {config_path}")
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file {config_path} not found.")
        raise
    except yaml.YAMLError as exc:
        logger.error(f"Error parsing configuration file {config_path}: {exc}")
        raise



def get_xiyan_config(db_config):
    dialect = db_config.get('dialect','mysql')
    xiyan_db_config = DBConfig(dialect=dialect,db_name=db_config['database'], user_name=db_config['user'], db_pwd=db_config['password'], db_host=db_config['host'], port=db_config['port'])
    return xiyan_db_config


global_config = get_yml_config()
mcp_config = global_config.get('mcp', {})
model_config = global_config['model']
global_db_config = global_config.get('database')
global_xiyan_db_config = get_xiyan_config(global_db_config)
dialect = global_db_config.get('dialect','mysql')



mcp = FastMCP("xiyan", **mcp_config)


@mcp.resource(dialect+'://'+global_db_config.get('database',''))
async def read_schema() -> str:

    db_engine = init_db_conn(global_xiyan_db_config)
    db_source = HITLSQLDatabase(
        engine=db_engine, 
        table_pattern=r"jn_cadre_info.*"  # 匹配所有以user_开头的表
    )
    return db_source.mschema.to_mschema()

@mcp.resource(dialect+"://{table_name}")
async def read_resource(table_name) -> str:
    """Read table contents."""
    config = global_db_config
    try:
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
                if cursor.description is None:
                    return f"No data found or query error for table {table_name}"
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                result = [",".join(map(str, row)) for row in rows]
                return "\n".join([",".join(columns)] + result)
                
    except Error as e:
        raise RuntimeError(f"Database error: {str(e)}")


def sql_gen_and_execute(db_env: DataBaseEnv, query: str):
    """
    Transfers the input natural language question to sql query (known as Text-to-sql) and executes it on the database.
     Args:
        query: natural language to query the database. e.g. 查询在2024年每个月，卡宴的各经销商销量分别是多少
    """

    #db_env = context_variables.get('db_env', None)
    prompt = f"""你现在是一名{db_env.dialect}数据分析专家，你的任务是根据参考的数据库schema和用户的问题，编写正确的SQL来回答用户的问题，生成的SQL用``sql 和```包围起来。
            【数据库schema】
            {db_env.mschema_str}
            
            【问题】
            {query}
            """
    #logger.info(f"SQL generation prompt: {prompt}")

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"用户的问题是: {query}"}
    ]
    param = {"model": model_config['name'], "messages": messages,"key":model_config['key'],"url":model_config['url']}

    try:
        response = call_openai_sdk(**param)
        content = response.choices[0].message.content
        sql_query = extract_sql_from_qwen(content)
        status, res = db_env.database.fetch(sql_query)
        if not status:
            for idx in range(3):
                error_info = str(res)  # 将res转换为字符串
                sql_query = sql_fix(db_env.dialect, db_env.mschema_str, query, sql_query, error_info)
                status, res = db_env.database.fetch(sql_query)
                if status:
                    break

        sql_res = db_env.database.fetch_truncated(sql_query,max_rows=100)
        markdown_res = db_env.database.trunc_result_to_markdown(sql_res)
        logger.info(f"SQL query: {sql_query}\nSQL result: {sql_res}")
        return markdown_res.strip()

    except Exception as e:
        return str(e)


def sql_fix(dialect: str, mschema: str, query: str, sql_query: str, error_info: str):
    system_prompt = '''现在你是一个{dialect}数据分析专家，需要阅读一个客户的问题，参考的数据库schema，该问题对应的待检查SQL，以及执行该SQL时数据库返回的语法错误，请你仅针对其中的语法错误进行修复，输出修复后的SQL。
        注意：
        1、仅修复语法错误，不允许改变SQL的逻辑。
        2、生成的SQL用```sql 和```包围起来。
        
        【数据库schema】
        {schema}
        '''.format(dialect=dialect, schema=mschema)
    user_prompt = '''【问题】
                {question}
                
                【待检查SQL】
                {sql}
                
                【错误信息】
                {sql_res}'''.format(question=query, sql=sql_query, sql_res=error_info)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    param = {"model": model_config['name'], "messages": messages,"key":model_config['key'],'url':model_config['url']}

    response = call_openai_sdk(**param)
    content = response.choices[0].message.content
    sql_query = extract_sql_from_qwen(content)

    return sql_query

def call_xiyan(query: str)-> str:
    """Fetch the data from database through a natural language query

    Args:
        query: The query in natual language
    """

    logger.info(f"Calling tool with arguments: {query}")
    try:
        db_engine = init_db_conn(global_xiyan_db_config)
        db_source = HITLSQLDatabase(
            engine=db_engine, 
            table_pattern=r"jn_cadre_info.*"  # 匹配所有以sys_或user_开头的表
        )
    except Exception as  e:

        return "数据库连接失败"+str(e)
    logger.info(f"Calling xiyan")
    env = DataBaseEnv(db_source)
    res = sql_gen_and_execute(env,query)

    return str(res)

@mcp.tool()
def get_data(query: str)-> list[TextContent]:
    """Fetch the data from database through a natural language query

    Args:
        query: The query in natural language
    """

    res=call_xiyan(query)
    return [TextContent(type="text", text=res)]


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> Response:
    """
    健康检查端点，用于监控服务器是否正常运行
    
    返回:
        - 服务器状态信息
        - MCP 版本信息
        - 数据库连接状态
        - 运行时间
    """
    import time
    import platform
    from datetime import datetime, timedelta
    
    # 获取服务器启动时间（如果没有记录，就使用当前时间）
    global server_start_time
    if not globals().get('server_start_time'):
        server_start_time = time.time()
    
    # 计算运行时间
    uptime_seconds = time.time() - server_start_time
    uptime = str(timedelta(seconds=int(uptime_seconds)))
    
    # 检查数据库连接
    db_status = "正常"
    try:
        db_engine = init_db_conn(global_xiyan_db_config)
        with db_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"异常: {str(e)}"
    
    # 收集系统信息
    system_info = {
        "操作系统": platform.system(),
        "Python版本": platform.python_version(),
        "处理器": platform.processor(),
        "主机名": platform.node()
    }
    
    # 构建状态信息
    status_info = {
        "状态": "正常运行",
        "服务名称": mcp.name,
        "MCP版本": "1.9.4",
        "启动时间": datetime.fromtimestamp(server_start_time).strftime("%Y-%m-%d %H:%M:%S"),
        "运行时长": uptime,
        "数据库状态": db_status,
        "系统信息": system_info,
        "传输模式": mcp_config.get("transport", "sse"),
        "API地址": f"http://{mcp_config.get('host', '0.0.0.0')}:{mcp_config.get('port', 8080)}"
    }
    
    return JSONResponse(status_info)

# 添加一个命令行工具来检查服务器状态
@mcp.tool()
def check_server_status() -> list[TextContent]:
    """
    检查服务器运行状态
    
    此工具返回服务器的运行状态、版本信息、数据库连接状态和运行时间等信息。
    可以用于监控和诊断服务器健康状况。
    """
    import time
    import platform
    from datetime import datetime, timedelta
    
    # 获取服务器启动时间（如果没有记录，就使用当前时间）
    global server_start_time
    if not globals().get('server_start_time'):
        server_start_time = time.time()
    
    # 计算运行时间
    uptime_seconds = time.time() - server_start_time
    uptime = str(timedelta(seconds=int(uptime_seconds)))
    
    # 检查数据库连接
    db_status = "正常"
    try:
        db_engine = init_db_conn(global_xiyan_db_config)
        with db_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"异常: {str(e)}"
    
    # 构建状态信息
    status_info = f"""
    服务器状态信息：
    ------------------------
    状态: 正常运行
    服务名称: {mcp.name}
    MCP版本: 1.9.4
    启动时间: {datetime.fromtimestamp(server_start_time).strftime("%Y-%m-%d %H:%M:%S")}
    运行时长: {uptime}
    数据库状态: {db_status}
    操作系统: {platform.system()}
    Python版本: {platform.python_version()}
    传输模式: {mcp_config.get("transport", "sse")}
    API地址: http://{mcp_config.get('host', '0.0.0.0')}:{mcp_config.get('port', 8080)}
    ------------------------
    """
    
    return [TextContent(type="text", text=status_info)]



def main():
    parser = argparse.ArgumentParser(description="Run MCP server.")
    parser.add_argument('transport', nargs='?', default=mcp_config.get('transport', 'sse'),
                        choices=['stdio', 'sse'],
                        help='Transport type (stdio or sse)')
    args = parser.parse_args()
    
    try:
        mcp.run(transport=args.transport)
        logger.info("MCP 服务已成功启动并运行")
    except Exception as e:
        logger.error(f"MCP 服务启动失败: {str(e)}")
        raise

if __name__ == "__main__":
    main()
