from flask import Flask, request, jsonify , abort
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
import socket
import time
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
api = Api(app)

# Configure Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://test:password@localhost:5432/swagger'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Prometheus Metrics
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='0.1.0')

class Root(Resource):
    def get(self):
        return {
            "version": "0.1.0",
            "date": int(time.time()),
            "kubernetes": False  # Set to True when deploying on Kubernetes
        }

class Lookup(Resource):
    def get(self):
        domain = request.args.get('domain')
        if not domain:
            abort(400, description="Domain parameter is required.")

        try:
            ipv4_address = socket.gethostbyname(domain)
            # Log the successful query into the database
            new_lookup = DomainLookup(domain=domain, ipv4_address=ipv4_address)
            db.session.add(new_lookup)
            db.session.commit()

            return jsonify(ipv4=ipv4_address)
        except socket.gaierror:
            return jsonify(error="Domain resolution failed"), 400
        except Exception as e:
            abort(500, description=str(e))

class Validate(Resource):
    def get(self):
        ip = request.args.get('ip')
        try:
            socket.inet_aton(ip)
            return {"valid": True}
        except socket.error:
            return {"valid": False}

class History(Resource):
    def get(self):
        queries = Query.query.order_by(Query.id.desc()).limit(20).all()
        return {'history': [{'domain': q.domain, 'result': q.result} for q in queries]}

class Health(Resource):
    def get(self):
        return {"status": "healthy"}

# Database Model
class Query(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), nullable=False)
    result = db.Column(db.String(255), nullable=False)

api.add_resource(Root, '/')
api.add_resource(Lookup, '/v1/tools/lookup')
api.add_resource(Validate, '/v1/tools/validate')
api.add_resource(History, '/v1/history')
api.add_resource(Health, '/metrics', '/health')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=3000)

