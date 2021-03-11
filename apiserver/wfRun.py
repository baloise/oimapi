# from workflows.Workflows import GenericWorkflow, Batch, BatchPhase
# from workflows.steps.WorkflowSteps import DeployItemStep, DummyStep, VerifyItemStep
import collections
from models.orders import Person, SbuType, OrderStateType, OrderItem, OrderStatus, Order  # noqa: F401,E501
from workflows.Factory import WorkflowFactory, OrderFactory
from workflows.Workflows import WorkflowTypes
from workflows.WorkflowContext import WorkflowContext
from models.orderTypes.OrderTypes import OrderType
from ourCloud.OcStaticVars import OC_CATALOGOFFERINGS, OC_CATALOGOFFERING_SIZES  # noqa F401
import logging
from dotenv import load_dotenv


load_dotenv()
logger = logging.getLogger()
logging.basicConfig(
    level=logging.DEBUG,
    style="{",
    datefmt="%d.%m.%Y %H:%M:%S",
    format="{asctime} {levelname}: {message}"
)

logger.setLevel(logging.DEBUG)

personPeter = Person(
            username='u12345',
            email='peter.parker@test.fake',
            sbu=SbuType.SHARED
        )
workflowFactory = WorkflowFactory()
orderFactory = OrderFactory()

rhel_item = OrderItem(OC_CATALOGOFFERINGS.RHEL7.cataloguename, OC_CATALOGOFFERING_SIZES.S2)
items = [rhel_item]
new_order = orderFactory.get_order(OrderType.CREATE_ORDER, items, personPeter)

wf = workflowFactory.get_workflow(WorkflowTypes.WF_CREATE_VM)
context = WorkflowContext(personPeter)
wf.set_context(context)
wf.set_order(new_order)

# bat_pre = Batch("pre-work", BatchPhase.RE_VERIFICATION, False)
# step1 = DummyStep("verify request")
# bat_pre.add_step(step1)

# bat_depl = Batch("deploy", BatchPhase.BE_PROCESSING, False)

# for item in new_order.get_items():
#     step = DeployItemStep(item)
#     bat_depl.add_step(step)

# bat_ver = Batch("verify", BatchPhase.BE_VERIFICATION, False)
# for item in new_order.get_items():
#     step = VerifyItemStep(item)
#     bat_ver.add_step(step)

# bat_tst = Batch("test", BatchPhase.TESTING, False)
# step4 = DummyStep("request testing")
# step5 = DummyStep("receive testing status")
# bat_tst.add_step(step4)
# bat_tst.add_step(step5)

# bat_hov = Batch("handover", BatchPhase.HANDOVER, False)
# step6 = DummyStep("complete request")
# bat_hov.add_step(step6)

# print("Defining Workflows")

# # batches will be ordered implicitly by BatchPhase
# wf = GenericWorkflow("new vm")
# wf.add_batch(bat_pre)
# wf.add_batch(bat_depl)
# wf.add_batch(bat_ver)
# wf.add_batch(bat_tst)
# wf.add_batch(bat_hov)

print("Executing Workflows...")
wf.execute()

# #### Factory example ####

# factory = WorkflowFactory()
# crwf = factory.get_workflow(WorkflowTypes.WF_CREATE_VM)
# crwf.add_batch(bat_depl)
# crwf.execute()

#  ################################### PLAYGROUND, please ignore below code ##########################################


class DeepChainMap(collections.ChainMap):
    'Variant of ChainMap that allows direct updates to inner scopes'

    def __setitem__(self, key, value):
        for mapping in self.maps:
            if key in mapping:
                mapping[key] = value
                return
        self.maps[0][key] = value

    def __delitem__(self, key):
        for mapping in self.maps:
            if key in mapping:
                del mapping[key]
                return
        raise KeyError(key)


di1 = {"k1": "v1"}
di2 = {"k2": "v2"}

map = DeepChainMap(di1)
map = map.new_child(di2)
map.maps = reversed(map.maps)
print("..................")
print("List Batches&their Actions {}".format(wf.get_name()))
for batch in wf.get_batches():
    print(" Batch {}".format(batch))
    for step in batch:
        print("  Action: {}".format(step.get_action()))

# print("Execute Workflows")
# wf.execute()

print("............")
