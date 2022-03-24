from starkware.cairo.common.hash_state import compute_hash_on_elements
from starkware.crypto.signature.signature import sign, verify


class Report:
    def __init__(self, report_context, observers, observations, signatures):
        self.report_context = report_context
        self.observers = observers
        self.observations = observations
        self.signatures = signatures

    def msg_hash(self):
        return compute_hash_on_elements([int(self.report_context, 16), int(self.observers, 16)] + self.observations)

    def sign_report(self, private_key):
        return sign(self.msg_hash(), private_key)

    def verify_report_signature(self, public_key, signature):
        return verify(self.msg_hash(), signature[0], signature[1], public_key)

    def __str__(self) -> str:
        return f"report_context: {self.report_context}\n observers: {self.observers}\n observations: {self.observations}"
