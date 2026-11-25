from .client_dialog import ClientDialog, ClientEditDialog, ClientViewDialog
from .order_dialog import OrderDialog
from .report_preview_dialog import ReportPreviewDialog
from .research_result_dialog import ResearchResultDialog
from .services_dialog import ServicesDialog
from .view_order_dialog import ViewOrderDialog

__all__ = [
    'OrderDialog', 'ViewOrderDialog',
    'ClientDialog', 'ClientEditDialog', 'ClientViewDialog',
    'ReportPreviewDialog', 'ServicesDialog', 'ResearchResultDialog',
]