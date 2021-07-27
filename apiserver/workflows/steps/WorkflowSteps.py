from abc import ABC, abstractmethod
from models.orders import OrderItem
from ourCloud.OurCloudHandler import OurCloudRequestHandler
from orchestra.OrchestraRequestHandler import OrchestraChangeHandler
from workflows.WorkflowContext import WorkflowContext
from oim_logging import get_oim_logger
from exceptions.WorkflowExceptions import StepException, RequestHandlerException, TransmitException
from random import sample
import traceback
from app import db
import time


class AbstractWorkflowStep(ABC):

    def __init__(self, action):
        self.action = action

    def get_action(self):
        return self.action

    @abstractmethod
    def execute(self, context: WorkflowContext):
        info = " execute action: {} for user {}".format(self.action, context.get_requester().email)
        logger = get_oim_logger()
        logger.info(info)


class DummyStep(AbstractWorkflowStep):
    def __init__(self):
        self.action = "dummy"

    def execute(self, context: WorkflowContext):
        info = "  Execute step: {} for user {}".format(self.action, context.get_requester().email)
        logger = get_oim_logger()
        logger.info(info)


class AwaitDeployStep(AbstractWorkflowStep):
    def __init__(self):
        self.action = "awaitdeploy"

    def execute(self, context: WorkflowContext):
        info = "  Execute step: {ac} for change {chg}".format(ac=self.action, chg=context.get_changeno())
        logger = get_oim_logger()
        logger.info(info)
        while True:
            # chstatus = self.getTicketStatus(context.get_changeno())
            chno = 'CH-0000014'  # chno = context.get_changeno()
            chstatus = self.getTicketStatus(chno)
            logger.info("Poll status of change {nr}: {chs}".format(nr=chno, chs=chstatus))
            if chstatus == "CH_REC":
                break
            time.sleep(10)

    def getTicketStatus(self, changeno: str):
        handler = OrchestraChangeHandler()
        return handler.select_change("TICKETNO", changeno)


class CreateCrStep(AbstractWorkflowStep):
    def __init__(self, item: OrderItem):
        self.action = "createcr"
        self.item = item

    def execute(self, context: WorkflowContext):
        info = "  Execute step: {ac} for item {itm}".format(ac=self.action, itm=self.item)
        logger = get_oim_logger()
        logger.info(info)
        crnr = self.getRandomChangeNr()
        context.set_changeno(crnr)
        logger.info("CR {nr} has been created".format(nr=crnr))

    def getRandomChangeNr(self) -> str:
        c = "{s}{i}".format(s="CH-", i=''.join(sample("123456789", 7)))
        return c


class DeployVmStep(AbstractWorkflowStep):
    def __init__(self, item: OrderItem):
        self.item = item
        self.action = "deploy"

    def execute(self, context: WorkflowContext):
        # extract details from order item
        # build request path
        # send request
        # handle response
        info = " Execute step: {ac} item {it} size '{si}' for user {us}".format(ac=self.action, it=self.item.get_cataloguename(),   # noqa E501
                                                                                si=self.item.get_size().catalogueid,
                                                                                us=context.get_requester().email)
        logger = get_oim_logger()
        logger.info(info)

        try:
            handler = OurCloudRequestHandler.getInstance()
            try:
                ocRequestId = handler.create_vm(item=self.item, requester=context.get_requester(), changeno=context.get_changeno())   # noqa E501
                self.persist_requestid(self.item, ocRequestId)
            except TransmitException as te:
                logger.error(te)
                raise StepException(te, self.item.order_id)  # use custom Exception here
            except Exception as e:
                track = traceback.extract_stack()
                logger.debug(track)
                errorStr = "Failed to create vm: {err} with parameters item='{itm}' requester='{rster}' ".format(err=e, itm=self.item.get_cataloguename().cataloguename, rster=context.get_requester())  # noqa 501
                logger.error(errorStr)
                raise  # StepException(errorStr, self.item.order_id)  # use custom Exception here
            else:
                info = f" Step result: {ocRequestId} ({self.action})"
                logger.info(info)
        except RequestHandlerException as e:
            errorStr = "Failed to instantiate request handler: {}".format(e)
            logger.error(errorStr)
            raise Exception(errorStr)
        else:
            logger.debug("Step completed ({})".format(self.action))

    def persist_requestid(self, item, reqid):
        anOrderItem = OrderItem.query.get(item.id)
        anOrderItem.set_backend_request_id(reqid)
        db.session.commit()


class VerifyItemStep(AbstractWorkflowStep):
    def __init__(self, item: OrderItem):
        self.item = item
        self.action = "verify"

    def execute(self, context: WorkflowContext):
        # check
        infoStr = "  Execute step: {} item {} size '{}' for user {}".format(self.action, self.item.get_cataloguename(),
                                                                            self.item.get_size().cataloguesize,
                                                                            context.get_requester().email)
        logger = get_oim_logger()
        logger.info(infoStr)
