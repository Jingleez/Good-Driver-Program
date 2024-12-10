from io import StringIO, BytesIO
from sqlalchemy import func
from driverProgram.models import PointTransaction, User
import csv

class ReportController:
    def __init__(self, db_session):
        self.db_session = db_session
        self.stream = StringIO()

    def driver_point_tracking(self, sponsor_id, start_date=None, end_date=None, driver_id=None):
        query = self.db_session.query(
            User.username.label('driver_name'),
            func.sum(PointTransaction.points).label('total_points'),
            PointTransaction.points.label('point_change'),
            PointTransaction.timestamp.label('date_of_change'),
            PointTransaction.reason.label('reason')
        ).join(
            User, PointTransaction.driver_id == User.id
        ).filter(
            PointTransaction.sponsor_id == sponsor_id
        )

        if start_date:
            query = query.filter(PointTransaction.timestamp >= start_date)
        if end_date:
            query = query.filter(PointTransaction.timestamp <= end_date)
        if driver_id:
            query = query.filter(PointTransaction.driver_id == driver_id)

        query = query.group_by(
            User.username, PointTransaction.points, PointTransaction.timestamp, PointTransaction.reason
        ).order_by(PointTransaction.timestamp.desc())

        return query.all()

    def write_csv(self, rows):
        writer = csv.writer(self.stream)
        writer.writerow(["Driver Name", "Total Points", "Point Change", "Date of Change", "Reason"])
        for row in rows:
            writer.writerow(row)

    def get_csv_file(self):
        mem = BytesIO()
        mem.write(self.stream.getvalue().encode('utf-8'))
        mem.seek(0)
        self.stream.close()
        return mem
