import lib
import json
import csv
import re
#remove this after testing
import time


class RQLAsync():
    def __init__(self):
        self.config = lib.ConfigHelper()
        self.csv_writer = lib.CsvWriter()
        self.pc_sess = lib.PCSession(self.config.pc_user, self.config.pc_pass, self.config.pc_cust,
                                     self.config.pc_api_base)

    def get_pcs_accounts(self,cloud_type):
        #pull in cloud accounts but only the relavant ones for the specified RQL
        self.url = "https://" + self.config.pc_api_base + "/cloud/name?onlyActive=true&cloudType=" + cloud_type
        self.pc_sess.authenticate_client()
        response = self.pc_sess.client.get(self.url)
        pcs_accounts_json = response.json()

        return pcs_accounts_json

    def insert_cloud_acct(self,src_str, insert_str, pos):
        #this inserts the cloud.account line into RQL 
        return f'{src_str[:pos]}{insert_str}{src_str[pos:]}'

    def rql_search(self):
        results = []
        body_params= {}
        page_number = 1

        #determine which cloud type the query is set to use
        match = re.search('\w*\s*=\s*\'(\w+)', self.config.pc_rql)
        if match:
            query_cloud_type = match.group(1)
            #calls the get accounts and uses the regex to only pull relavant cloud accts
            pcs_accounts = self.get_pcs_accounts(query_cloud_type)
        else:
            print("RQL doesn't appear to be formatted correctly, please double check and try again.\n")
        
        for acct in pcs_accounts:
            if acct['cloudType'] == query_cloud_type:
                pos = self.config.pc_rql.find(' api.name')
                #needed to use .replace with literal to backspace single quotes in account names
                mod_rql = self.insert_cloud_acct(self.config.pc_rql,' cloud.account = ' + '\'' + acct['name'].replace(r"'",r"\'") + '\'' + ' AND',pos)

                while page_number == 1 or 'pageToken' in body_params:
                    self.url = "https://" + self.config.pc_api_base + "/search/config"
                    self.pc_sess.authenticate_client()
                    payload = json.dumps(
                        {"withResourceJson":"false",
                        "limit": 100,
                        "timeRange": {
                            "type":"relative",
                            "value": {
                                "unit": "hour",
                                "amount": 24
                            },
                            "relativeTimeType": "BACKWARD"
                        },
                        "query": mod_rql
                    })

                    response = self.pc_sess.client.post(self.url,payload)
                    if response == '400':
                        print('Something appears to be wrong with RQL query')
                    else:
                        resp_json = response.json()
                        if 'items' in resp_json['data']:
                            results.extend(resp_json['data']['items'])
                        if 'nextPageToken' in resp_json:
                            body_params['pageToken'] = resp_json['nextPageToken']
                        else:
                            body_params.pop('pageToken', None)

                        page_number += 1

            for res in results:
                print(res)
                time.sleep(60) 

    def run(self):
        self.rql_search()

def main():
    RQL_Async = RQLAsync()
    RQL_Async.run()

if __name__ == "__main__":
    main()
