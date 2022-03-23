from starkware.cairo.common.hash_state import compute_hash_on_elements
from starkware.crypto.signature.signature import sign


class Report:
    def __init__(self, report_context, observers, observations):
        self.report_context = report_context
        self.observers = observers
        self.observations = observations

    def msg_hash(self):
        return compute_hash_on_elements([self.report_context, self.observers] + self.observations)

    def sign_report(self, private_key):
        return sign(self.msg_hash(), private_key)

    def __str__(self) -> str:
        return f"report_context: {self.report_context}\n observers: {self.observers}\n observations: {self.observations}"
