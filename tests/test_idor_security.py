import sys
import os
import unittest
import uuid

# Ensure backend directory is in Python path for app imports
backend_path = os.path.abspath('backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient
# pyrefly: ignore [missing-import]
from app.main import app as fastapi_app
# pyrefly: ignore [missing-import]
from app.db.database import initialize_database, Base, engine
# pyrefly: ignore [missing-import]
from app.models.user import User
# pyrefly: ignore [missing-import]
from app.models.tender import Tender
# pyrefly: ignore [missing-import]
from app.models.bid import Bid
# pyrefly: ignore [missing-import]
from app.models.document import Document
# pyrefly: ignore [missing-import]
from app.models.requirement import Requirement
# pyrefly: ignore [missing-import]
from app.core.security import create_access_token

class TestIDORSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize_database()
        # pyrefly: ignore [missing-import]
        import app.models
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(fastapi_app)

        # Create unique User A (Bidder)
        cls.user_a_id = uuid.uuid4()
        cls.email_a = f"user_a_{str(uuid.uuid4())[:8]}@bidder.com"
        cls.token_a = create_access_token(subject=str(cls.user_a_id), role="BIDDER")

        # Create unique User B (Bidder)
        cls.user_b_id = uuid.uuid4()
        cls.email_b = f"user_b_{str(uuid.uuid4())[:8]}@bidder.com"
        cls.token_b = create_access_token(subject=str(cls.user_b_id), role="BIDDER")

        # pyrefly: ignore [missing-import]
        from app.db.database import SessionLocal
        with SessionLocal() as db:
            user_a = User(
                id=cls.user_a_id,
                full_name="User A (Compliant Bidder)",
                email=cls.email_a,
                password_hash="",
                role="BIDDER",
                is_active=True
            )
            user_b = User(
                id=cls.user_b_id,
                full_name="User B (Unauthorized Bidder)",
                email=cls.email_b,
                password_hash="",
                role="BIDDER",
                is_active=True
            )
            db.add_all([user_a, user_b])

            # Seed Tender
            cls.tender_id = f"TENDER-IDOR-{str(uuid.uuid4())[:6]}"
            tender = Tender(
                id=cls.tender_id,
                title="IDOR Security Test Tender",
                description="Tender created strictly for authorization testing",
                category="General Procurement",
                department="Procurement",
                tender_type="Custom Bid",
                budget_limit=5000000.0,
                status="Active"
            )
            db.add(tender)

            # Seed Requirement
            cls.req_id = uuid.uuid4()
            req = Requirement(
                id=cls.req_id,
                tender_id=cls.tender_id,
                code="GST",
                description="GST Certificate",
                is_mandatory=True
            )
            db.add(req)

            # Seed Bid for User A
            cls.bid_a_id = uuid.uuid4()
            bid_a = Bid(
                id=cls.bid_a_id,
                tender_id=cls.tender_id,
                bidder_id=cls.user_a_id,
                status="Pending",
                compliance_score=85.0
            )
            db.add(bid_a)

            # Seed Document for User A
            cls.doc_a_id = uuid.uuid4()
            doc_a = Document(
                id=cls.doc_a_id,
                bid_id=cls.bid_a_id,
                requirement_id=cls.req_id,
                document_type="GST_CERTIFICATE",
                original_filename="user_a_gst.pdf",
                storage_path=f"{cls.user_a_id}/{cls.bid_a_id}/GST/{cls.doc_a_id}_gst.pdf",
                mime_type="application/pdf",
                file_size=1024,
                file_hash="dummyhash_user_a",
                document_status="UPLOADED",
                uploaded_by=cls.user_a_id
            )
            db.add(doc_a)
            db.commit()

    def test_01_user_a_can_access_own_bid(self):
        """User A should be able to view their own bid submission."""
        headers = {"Authorization": f"Bearer {self.token_a}"}
        res = self.client.get(f"/api/bids/{self.bid_a_id}", headers=headers)
        self.assertEqual(res.status_code, 200, f"User A could not access own bid: {res.text}")

    def test_02_user_b_cannot_access_user_a_bid(self):
        """User B attempting to view User A's bid must receive 403 Forbidden or 404 Not Found."""
        headers = {"Authorization": f"Bearer {self.token_b}"}
        res = self.client.get(f"/api/bids/{self.bid_a_id}", headers=headers)
        self.assertIn(res.status_code, [403, 404], f"IDOR Vulnerability! User B accessed User A bid: {res.text}")

    def test_03_user_b_cannot_access_user_a_document(self):
        """User B attempting to view or download User A's document must be blocked (403/404/405)."""
        headers = {"Authorization": f"Bearer {self.token_b}"}
        res = self.client.get(f"/api/documents/{self.doc_a_id}", headers=headers)
        self.assertIn(res.status_code, [403, 404, 405], f"IDOR Vulnerability! User B accessed User A document: {res.text}")

    def test_04_user_b_my_bids_does_not_contain_user_a_data(self):
        """User B requesting GET /api/bids/my-bids must see only User B's data (0 bids)."""
        headers = {"Authorization": f"Bearer {self.token_b}"}
        res = self.client.get("/api/bids/my-bids", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        bid_ids = [b["id"] for b in data]
        self.assertNotIn(str(self.bid_a_id), bid_ids, "User B saw User A's bid in my-bids!")

if __name__ == "__main__":
    unittest.main()
