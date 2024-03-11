import calendar
from typing import Optional, List
from datetime import datetime 
import asyncio
import requests
import json
from typing import Tuple
import xml.etree.ElementTree as ET
import time
from requests.auth import HTTPProxyAuth

#definimos una http si existe conexion a internet a traves de un proxy. 


class AppConfig:
    _config_data = None

    @staticmethod
    def _load_config():
        try:
            with open('appsettings.json', 'r') as file:
                AppConfig._config_data = json.load(file)
        except FileNotFoundError:
            # Manejar la falta de archivo de configuración aquí o lanzar una excepción según tu lógica.
            AppConfig._config_data = {}

    @staticmethod
    def get_monday_config():
        if AppConfig._config_data is None:
            AppConfig._load_config()
        return AppConfig._config_data.get('MondayApi', {})

    @staticmethod
    def get_jira_config():
        if AppConfig._config_data is None:
            AppConfig._load_config()
        return AppConfig._config_data.get('JiraApi', {})

    @staticmethod
    def get_tempo_config():
        if AppConfig._config_data is None:
            AppConfig._load_config()
        return AppConfig._config_data.get('TempoApi', {})

    @staticmethod
    def get_proxy_config():
        if AppConfig._config_data is None:
            AppConfig._load_config()
        return AppConfig._config_data.get('Proxy', {})



class http_Factory:
    def __init__(self):
        # Lee la configuración desde appsettings.json

        self.app_settings= AppConfig.get_proxy_config()

        self.proxy_url = self.app_settings.get('Url')
        self.proxy_user = self.app_settings.get('Username')
        self.proxy_password = self.app_settings.get('Password')
        
        # Configura las cabeceras (headers) comunes
        

    def make_request(self, url, method=None, params=None, data=None, headers=None):
        if data is not None:
            # Convierte el diccionario a JSON si hay datos
            data = json.dumps(data)

        if self.proxy_url and self.proxy_user and self.proxy_password:
            # Usa un proxy si se proporcionan las configuraciones
            proxies = {
                'http': f'http://{self.proxy_url}',
                'https': f'https://{self.proxy_url}',
            }
            auth = HTTPProxyAuth(self.proxy_user, self.proxy_password)
            response = requests.request(method, url, params=params, data=data, proxies=proxies, auth=auth, headers=headers)
        else:
            # Sin proxy
            response = requests.request(method, url, params=params, data=data, headers=headers)

        return response

    
# Definimos la clase que llama al servidor de tempo y se trae toda la carga de horas en un periodo de tiempo establecido.
class CallWorklogInTempoServer:
    def __init__(self):
        # Lee la configuración desde appsettings.json

        self.app_settings= AppConfig.get_tempo_config()

        self.tempo_url = self.app_settings.get('UrlTempo')
        self.tempo_token = self.app_settings.get('TokenTempo')
        
        # Configura las cabeceras (headers) comunes

    async def CallWorklogInServer(self):
        # Parámetros para la query de Tempo
        date_from, date_to = self.resolver_fechas()
        base_url = self.tempo_url  # Reemplaza con tu URL real
        format_type = "xml"
        diff_only = "true"
        tempo_api_token = self.tempo_token  # Reemplaza con tu token real
        add_issue_details = "true"
        add_user_details = "true"
        add_billing_info = "true"

        # Construir la URL con los parámetros
        params = {
            "dateFrom": date_from,
            "dateTo": date_to,
            "format": format_type,
            "diffOnly": diff_only,
            "addIssueDetails": add_issue_details,
            "addUserDetails": add_user_details,
            "tempoApiToken": tempo_api_token,
            "addBillingInfo": add_billing_info
        }

        url = f"{base_url}?{requests.compat.urlencode(params)}"

        headers = {"Accept":"aplication/xml"}
        r = http_Factory()
        
        response = r.make_request(url=url,method="GET",params=None, data=None, headers=None)

        if response.status_code==200:
            
            xml_content = response.text            
            #worklog_server = self.parse_xml(response)            
            return xml_content
        else:     
            return None






    def resolver_fechas(self) -> Tuple[str,str]:
         # La fecha de la petición funciona así: toma el día actual y toma el primer día del mes anterior.
        # Si hoy es el 1 de noviembre, consulta las fechas del 1/11 hasta el 1/10, dando una ventana de 30 días.
        # Si el día de hoy es 30 de noviembre, sigue tomando hasta el 1/10, con una ventana de 60 días.
        # El primero de diciembre llama hasta el 1/11, volviendo al mínimo de 30 días de consulta.

        day_today = datetime.today()
        if day_today.month == 1:
            first_day_of_last_month = datetime(day_today.year-1,12, 1)
        else:
            first_day_of_last_month = datetime(day_today.year, day_today.month - 1, 1)
            
        date_initial = first_day_of_last_month.strftime("%Y-%m-%d")
        
        date_to = day_today.strftime("%Y-%m-%d")
        return date_initial, date_to

    def parse_xml(self, xml_content):
        # Aquí deberías implementar la lógica para parsear el XML y devolver el objeto Worklogs.
        # El código siguiente es un ejemplo simple y puede necesitar ajustes según la estructura real del XML.
        
        root = ET.fromstring(xml_content)
        issue_key = root.find("issue_key").text
                
        if worklogs_element is not None:
            worklogs = Worklogs.from_xml_element(worklogs_element)
            return WorklogServer(worklogs)
        else:
            return None
    

# Definimos la clase que llama a Monday e identifica la tabla con nombre "jira-tempo". Eso nos da el tablero objetivo.
class CallApiMondayBoardsWithTempo:
    def __init__(self):
        # Lee la configuración desde appsettings.json

        self.app_settings= AppConfig.get_monday_config()

        self.monday_url = self.app_settings.get('UrlMonday')
        self.monday_token = self.app_settings.get('TokenMonday')
        
        # Configura las cabeceras (headers) comunes
    async def CallData(self):
        listWithTempoConex = []

        #baseUrl = "https://api.monday.com/v2"  # Reemplaza con tu URL de API
        # username = "isrrael.rios@protechcompany.com"
        #apiToken = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjI5Nzk5MjQ2MiwiYWFpIjoxMSwidWlkIjo0ODk2NzEwNywiaWFkIjoiMjAyMy0xMS0yMlQxMjo1MTozOS4yMTJaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MTYzNDA0MjEsInJnbiI6InVzZTEifQ.kO3CGGb0GhA6svU1QEmaL_vpmekMTTdzoHUYb_E2LbU"  # Reemplaza con tu token
       
        query = """
                query {
                    boards(limit: 600) {
                        id,
                        workspace_id,
                        name,
                        type
                    }
                }
            """

        # Configurar la solicitud HTTP
        custom_headers = {"Content-type": "application/json", "Authorization": f"Bearer {self.monday_token}"}
       
        custom_data = {"query":query}
       
        

        r = http_Factory()
        respuesta = r.make_request(url=self.monday_url,method="POST", params=None, data=custom_data, headers=custom_headers)
        

        #r= requests.post(url=baseUrl, data=json.dumps(data), headers=headers)
        

        if respuesta.ok:
            # Leer y analizar la respuesta JSON
            
            responseData = respuesta.json()                   
         
            for board in responseData["data"]["boards"]:
                if "jira-tempo" in board["name"].lower() and board["type"] == "board":
                    listWithTempoConex.append(board)

        else:
            print(respuesta.text)
  
        
        return listWithTempoConex

# entidades de account, project y entry usadas para cerar el resumen inicial de los worklogs


class Entry:
    def __init__(self, month: Optional[str], hour: int) -> None:
        self.month = month
        self.hour = hour

class Account:
    def __init__(self, name_account: Optional[str]) -> None:
        self.name_account = name_account
        self.entries: List[Entry] = []



# lista llenado de lista de resumen de horas en account y projecto

summary_accounts:List[Account] = []

def add_or_update_account(worklog):
    # La cuenta no existe, agregar nueva cuenta
    billing_element = worklog.find('Billing')   

    name_value = billing_element.get('name')

    existing_account = next((acc for acc in summary_accounts if acc.name_account == name_value), None)

    # Aislar el mes de cada carga de horas
    month_worklog = datetime.strptime(worklog.find('work_date').text, "%Y-%m-%d")
    month = calendar.month_name[month_worklog.month]
    year = str(month_worklog.year)[2:]
    month_id = f"{month}_{year.lower()}"
    
    # Convierte en entero la carga de horas
    horas = worklog.find('hours').text
    horas_float = float(horas)
    horas_int = int(horas_float)

    if existing_account:
        # La cuenta ya existe, verificar si el mes ya existe en la cuenta
        existing_month = next((entry for entry in existing_account.entries if entry.month == month_id), None)

        if existing_month:
            # El mes existe, agregar horas al mes existente
            existing_month.hour += horas_int
        else:
            # El mes no existe, agregar nueva entrada al mes en la cuenta
            existing_account.entries.append(Entry(month=month_id, hour=horas_int))
    else:
        new_account = Account(name_account= name_value)
        new_account.entries.append(Entry(month=month_id, hour=horas_int))
        summary_accounts.append(new_account)



async def find_project_and_account_in_table(account, project, monday_board_id):
        
    query = f"""
        query nombres {{
            items_page_by_column_values(
                limit: 50
                board_id: {monday_board_id}
                columns: [
                    {{column_id: "name", column_values: ["{account}"]}},
                    {{column_id: "proyecto", column_values: ["{project}"]}}
                ]
            ) {{
                cursor
                items {{
                    id
                    name
                    column_values {{
                        value
                        id
                    }}
                }}
            }}
        }}
    """

    monday_config = AppConfig.get_monday_config()
    monday_token = monday_config.get('TokenMonday')
    monday_url = monday_config.get('UrlMonday')
    
    request_data = {"query":query}
    
    custom_headers = {
        "Authorization": f"Bearer {monday_token}",  # Asegúrate de definir TokenMonday
        "API-Version": "2023-10",
        'Content-Type': 'application/json',
    }
    
    r2= http_Factory()
    response2 = r2.make_request(url= monday_url, method="POST", params=None, data=request_data, headers=custom_headers)
        
    #response = requests.post(url=url_base,data=request_data,headers=custom_headers)
    try:
        if response2.status_code == 200:
            data = response2.json()
           
            
            if len(data['data']['items_page_by_column_values']['items']) == 0:
                return False, data

            return True, data

        else:
            response_content = response2.text
            return True, response_content

    except requests.RequestException as ex:
        print(f"Error de comunicación: {str(ex)}")
        return True, None

    except Exception as ex:
        print(f"Error inesperado: {str(ex)}")
        return True, None


# metodo que busca una cuneta y devuelve true si existe 

async def find_account_in_table(account, monday_board_id):
    query = f"""
        query nombres {{
            items_page_by_column_values(
                limit: 50
                board_id: {monday_board_id}
                columns: [{{column_id: "name", column_values: ["{account.name_account}"]}}
            ]) {{
                cursor
                items {{
                    id
                    name
                    column_values {{
                        value
                        id
                    }}
                }}
            }}
        }}
    """
    request_data = {"query": query}

    monday_config = AppConfig.get_monday_config()
    monday_token = monday_config.get('TokenMonday')
    monday_url = monday_config.get('UrlMonday')

    
    headers = {
        "Authorization": f"Bearer {monday_token}",
        "API-Version": "2023-10",
        "Content-Type": "application/json",
    }

    try:
        r= http_Factory()

        response = r.make_request(url=monday_url, method="POST", params=None,data=request_data, headers=headers) # requests.post(url=url_base, json=request_data, headers=headers)
        
        
        if response.status_code == 200:
            data = response.json()           

            if len(data['data']['items_page_by_column_values']['items']) == 0:
                return False, data

            return True, data
        else:
            response_content = response.text
            response_data = requests.Response(json.loads(response_content))
            return True, response_data
    except requests.RequestException as ex:
        print(f"Error de comunicación: {str(ex)}")
        return True, None
    except Exception as ex:
        print(f"Error inesperado: {str(ex)}")
        return True, None


# clase para actualizar elemento en monday.com


class UpdateItemInMonday:    
    async def update_item(self, entry, item, board_id):
        # Se establece el mes actual
        mes_actual = datetime.now().strftime("%B")
        
        #mes_worklog = project.entries[0].month

        #hora = project.entries[0].hour
        hora_item = 0
        hora_total = 0

        # Se utiliza time.sleep en lugar de Task.Delay
        time.sleep(2)

        query = f"""
            mutation update {{
                change_simple_column_value(
                    item_id: {item['data']['items_page_by_column_values']['items'][0]['id']}
                    board_id: {board_id},
                    column_id: "{entry.month.lower()}",
                    value: "{entry.hour}"
                ) {{
                    id
                }}
            }}
        """
        

        request_data = {"query": query}

        monday_config = AppConfig.get_monday_config()
        monday_token = monday_config.get('TokenMonday')
        monday_url = monday_config.get('UrlMonday')
        
        headers = {
            "Authorization": f"Bearer {monday_token}",
            "Content-Type": "application/json",
        }

        try:
            r=http_Factory()

            response = r.make_request(url=monday_url,method="POST", params=None, data=request_data, headers=headers) #requests.post(url=api_url, json=request_data, headers=headers)
            
            if response.status_code == 200:
                # Procesar la respuesta exitosa
                pass
            else:
                # Procesar la respuesta de error, si es necesario
                response_content = response.text
                response_data = json.loads(response_content)

        except requests.RequestException as ex:
            # Capturar errores de red o problemas de comunicación
            print(f"Error de comunicación: {str(ex)}")
        except Exception as ex:
            # Capturar otras excepciones inesperadas
            print(f"Error inesperado: {str(ex)}")

class UpdateItemSpecialInMonday:    
    async def update_item(self, entry, item, board_id):
        # Se establece el mes actual
        #//itemId = item['data']['items_page_by_column_values']['items']
        #itemIdToChange = itemId[0]['id']
        mes_actual = datetime.now().strftime("%B")
        
        mes_worklog = entry.month

        hora = entry.hour
        hora_item = 0
        hora_total = 0

        # Se utiliza time.sleep en lugar de Task.Delay
        time.sleep(2)

        query = f"""
            mutation update {{
                change_simple_column_value(
                    item_id: {item}
                    board_id: {board_id},
                    column_id: "{entry.month.lower()}",
                    value: "{entry.hour}"
                ) {{
                    id
                }}
            }}
        """
        
        request_data = {"query": query}

        monday_config = AppConfig.get_monday_config()
        monday_token = monday_config.get('TokenMonday')
        monday_url = monday_config.get('UrlMonday')
        
        
        headers = {
            "Authorization": f"Bearer {monday_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url=monday_url, json=request_data, headers=headers)
            
            if response.status_code == 200:
                # Procesar la respuesta exitosa
                pass
            else:
                # Procesar la respuesta de error, si es necesario
                response_content = response.text
                response_data = json.loads(response_content)

        except requests.RequestException as ex:
            # Capturar errores de red o problemas de comunicación
            print(f"Error de comunicación: {str(ex)}")
        except Exception as ex:
            # Capturar otras excepciones inesperadas
            print(f"Error inesperado: {str(ex)}")

# metodo para crear un item que no existe en monday.com


async def create_item_special(account, board_id):

    monday_config = AppConfig.get_monday_config()
    monday_token = monday_config.get('TokenMonday')
    monday_url = monday_config.get('UrlMonday')
    
    await asyncio.sleep(2)  # Pausa de 2 segundos

    query = f"""
        mutation usr {{
            create_item(item_name: "{account}", board_id: {board_id}) {{
                id
            }}
        }}    """

    request_data = {"query": query}
    
    headers = {
        "Authorization": f"Bearer {monday_token}",  # Asegúrate de definir TokenMonday
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url=monday_url, json=request_data, headers=headers)

        if response.status_code == 200:
            response_json = response.json()
            item_id = response_json.get("data", {}).get("create_item", {}).get("id")
            return item_id

        else:
            response_content = response.text
            response_data = json.loads(response_content)
            return None

    except requests.RequestException as ex:
        print(f"Error de comunicación: {str(ex)}")
        return None

    except Exception as ex:
        print(f"Error inesperado: {str(ex)}")
        return None

# Función auxiliar para convertir el objeto 'project' a una cadena JSON válida
def create_json(project):
    # Implementa la lógica para convertir el objeto 'project' a una cadena JSON válida
    # DateTime mesWorklog = DateTime.Parse(result.WorkDate.ToString());
    # string mesW = mesWorklog.ToString("MMMM");

    sb = []

    # Abro json
    sb.append("{")

    # sb.Append($"\\\"{entry.Month}\\\" : {entry.Hour},")
    sb.append(f'\\"proyecto\\" : \\"{project}\\"')

    # cierro json
    sb.append("}")

    # Concateno la lista en una cadena y reemplazo saltos de línea
    v = "".join(sb).replace("\n", "")
    return v



# Método principal del script
async def main():
    
    call = CallApiMondayBoardsWithTempo()
    BoardsWithTempo = await call.CallData()  # Corregido: añade los paréntesis

    callWorklogs = CallWorklogInTempoServer()
    allWorklogsXml = await callWorklogs.CallWorklogInServer()
    root = ET.fromstring(allWorklogsXml)
    list_worklogs=root.findall('worklog')
    
    for worklog in list_worklogs:
        add_or_update_account(worklog=worklog)  
    

    for e in summary_accounts: 
        #entramos aqui si no existe proyecto y cuenta. ahora buscamos si solo existe account
              
        exist_account_only , data_response = await find_account_in_table(account=e, monday_board_id=BoardsWithTempo[0]['id'])
        
        if exist_account_only:
            for month in e.entries:
                update_item = UpdateItemInMonday()
                await update_item.update_item( entry=month, item=data_response, board_id= BoardsWithTempo[0]['id'])
                        
        else:    
            item_created = await create_item_special(account=e.name_account, board_id=BoardsWithTempo[0]['id'])
            if item_created != None:
                for month in e.entries:
                    update_item_special = UpdateItemSpecialInMonday()
                    await update_item_special.update_item( entry=month, item=item_created, board_id= BoardsWithTempo[0]['id'])
            
           
# Ejecutar el bucle de eventos asyncio
asyncio.run(main())



