from kubernetes import client, config
from openshift.dynamic import DynamicClient
import kubernetes.config
import traceback
import sys
import datetime
from datetime import timedelta
from pytz import timezone

def get_client(**kwargs):
    try:
        k8s_client = config.new_client_from_config()
    except config.config_exception.ConfigException:
        traceback.print_exc()
        sys.exit(1)

    return DynamicClient(k8s_client)

token_auth = dict(
    api_key={'authorization': 'Bearer {}'.format('<api-token>')},
    host='<host>',
    verify_ssl=False
)

def check_monitoring_time(event_time):
    previous_date = datetime.datetime.utcnow() - timedelta(minutes=5)

    return event_time > previous_date

nodeEventList = ['NodeNotReady','FailedNodeAllocatableEnforcement','HostPortConflict','ContainerFCFailed','Rebooted']

def main():
    try:
        client = get_client(**token_auth)
        v1_events = client.resources.get(api_version='events.k8s.io/v1beta1', kind='Event')

        event_list = v1_events.get()

        for event in event_list.items:
            converted_date = datetime.datetime.strptime(event.metadata.creationTimestamp,"%Y-%m-%dT%H:%M:%SZ")
            converted_date_utc = pytz.utc.localize(converted_date)

            if check_monitoring_time(converted_date) == True:
                converted_date_kst = converted_date_utc.astimezone(timezone('Asia/Seoul')).strftime("%Y-%m-%dT%H:%M:%SZ")

                if event.regarding.kind == "Node" and event.reason in nodeEventList:
                    print(converted_date_kst,"|",event.regarding.kind,"|",event.metadata.name,"|",event.reason,"|",event.note)
            
    except Exception as e:
        traceback.print_exc()

if __name__ == '__main__':
    main()
