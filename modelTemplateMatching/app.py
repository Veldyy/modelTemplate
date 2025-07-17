from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
from db import get_connection  # assumed reusable DB module
from flask import send_from_directory
from takepicture_process import process_image_route
from stream_process import stream_process

app = Flask(__name__)

@app.route('/bukti/<path:filename>')
def serve_bukti(filename):
    return send_from_directory('bukti', filename)

@app.route("/api/informasi", methods=["GET"])
def get_informasi():
    try:
        # Connect to database
        connection = get_connection()
        with connection:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM informasi"
                cursor.execute(sql)
                results = cursor.fetchall()

        return jsonify({
            'statusCode': 200,
            'message': 'Data berhasil diambil.',
            'data': results
        })

    except Exception as e:
        return jsonify({
            'statusCode': 500,
            'message': f'Gagal mengambil data: {str(e)}',
            'data': []
        })
    
@app.route("/api/authenticate", methods=["POST"])
def authenticate():
    try:
        data = request.form
        email = data.get('email')
        password = data.get('password')

        # Basic validation
        if not email or not password:
            return jsonify({
                'statusCode': 400,
                'message': 'Email dan password harus diisi.'
            })

        # Connect to database
        connection = get_connection()
        with connection:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM user WHERE email=%s AND password=%s"
                cursor.execute(sql, (email, password))
                user = cursor.fetchone()

                if user:
                    normalized_data = {
                        'id': user['id_user'],
                        'nama_lengkap': user['nama_lengkap'],
                        'email': user['email'],
                        'password': user['password'],
                        'tanggal_lahir': user['tanggal_lahir'],
                        'role': 'user'
                    }
                    return jsonify({
                        'statusCode': 200,
                        'message': 'Login berhasil',
                        'data': normalized_data
                    })

        return jsonify({
            'statusCode': 401,
            'message': 'email or password salah'
        })

    except Exception as e:
        return jsonify({
            'statusCode': 500,
            'message': f'Login gagal: {str(e)}'
        })


@app.route("/api/register", methods=["POST"])
def register_user():
    try:
        # Use form to support x-www-form-urlencoded
        nama_lengkap = request.form.get('nama_lengkap')
        email = request.form.get('email')
        password = request.form.get('password')
        tanggal_lahir = request.form.get('tanggal_lahir')

        if not nama_lengkap or not email or not password or not tanggal_lahir:
            return jsonify({
                'statusCode': 400,
                'message': 'Semua field harus diisi.',
                'data': None
            })

        conn = get_connection()
        with conn:
            with conn.cursor() as cursor:
                # Check if email already exists
                sql_check = "SELECT * FROM user WHERE email = %s"
                cursor.execute(sql_check, (email,))
                if cursor.fetchone():
                    return jsonify({
                        'statusCode': 400,
                        'message': 'Email sudah digunakan.',
                        'data': None
                    })

                # Insert new user
                sql_insert = """
                    INSERT INTO user (nama_lengkap, email, password, tanggal_lahir)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql_insert, (nama_lengkap, email, password, tanggal_lahir))
                conn.commit()

                return jsonify({
                    'statusCode': 200,
                    'message': 'Registrasi berhasil.'
                })

    except Exception as e:
        return jsonify({
            'statusCode': 500,
            'message': f'Registrasi gagal: {str(e)}',
            'data': None
        })

@app.route("/api/riwayat-bukutamu", methods=["POST"])
def get_riwayat_pendaftaran():
    try:
        id_user = request.form.get("id_user", type=int)

        if not id_user or id_user <= 0:
            return jsonify({
                'statusCode': 400,
                'message': 'ID user tidak valid.',
                'data': []
            })

        conn = get_connection()
        with conn:
            with conn.cursor() as cursor:
                query = """
                    SELECT 
                        p.*,
                        s.id_user, s.nama_lengkap, s.email, s.tanggal_lahir,
                        b.id_bukti, b.foto_bukti, b.tanggal_cetak
                    FROM pendaftaran p
                    LEFT JOIN user s ON p.id_user = s.id_user
                    LEFT JOIN bukti_bukutamu b ON p.id_bukutamu = b.id_bukutamu
                    WHERE p.id_user = %s
                    ORDER BY p.tanggal_daftar DESC
                """
                cursor.execute(query, (id_user,))
                rows = cursor.fetchall()

        data = []
        for row in rows:
            item = {
                'id_bukutamu': row['id_bukutamu'],
                'tanggal_daftar': row['tanggal_daftar'],
                'keperluan': row.get('keperluan'),
                'nik': row['nik'],
                'nama': row['nama'],
                'pekerjaan': row['pekerjaan'],
                'alamat': row['alamat'],
                'no_telp': row['no_telp'],
                'user': {
                    'id_user': row['id_user'],
                    'nama_lengkap': row['nama_lengkap'],
                    'email': row['email'],
                    'tanggal_lahir': row['tanggal_lahir']
                },
                'bukti_bukutamu': {
                    'id_bukti': row['id_bukti'],
                    'foto_bukti': row['foto_bukti'],
                    'tanggal_cetak': row['tanggal_cetak']
                } if row['foto_bukti'] else None
            }
            data.append(item)

        return jsonify({
            'statusCode': 200,
            'message': 'Riwayat pendaftaran berhasil diambil.',
            'data': data
        })

    except Exception as e:
        return jsonify({
            'statusCode': 500,
            'message': f'Gagal mengambil riwayat: {str(e)}',
            'data': []
        })

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'bukti')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/submit-bukutamu', methods=['POST'])
def pendaftaran_with_bukti():
    required_fields = [
        'idUser', 'nik', 'nama', 'pekerjaan',
        'no_telp', 'alamat', 'keperluan', 'tanggal_daftar'
    ]

    data = request.form
    file = request.files.get('foto_bukti')

    # Validasi field kosong
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                'statusCode': 400,
                'message': f"Field '{field}' tidak boleh kosong."
            }), 400

    # Validasi file
    if file is None or file.filename == '':
        return jsonify({
            'statusCode': 400,
            'message': 'File bukti wajib diunggah.'
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            'statusCode': 415,
            'message': 'Hanya file JPG atau PNG yang diperbolehkan.'
        }), 415

    # Persiapan penyimpanan file
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    ext = file.filename.rsplit('.', 1)[1].lower()
    new_filename = f"bukti_{os.urandom(6).hex()}.{ext}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)

    try:
        connection = get_connection()
        connection.begin()

        with connection.cursor() as cursor:
            # Insert ke tabel pendaftaran
            insert_sql = """
                INSERT INTO pendaftaran (id_user, nik, nama, pekerjaan, no_telp, alamat, tanggal_daftar, keperluan)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (
                int(data['idUser']),
                data['nik'],
                data['nama'],
                data['pekerjaan'],
                data['no_telp'],
                data['alamat'],
                data['tanggal_daftar'],
                data['keperluan']
            ))

            id_bukutamu = connection.insert_id()

            # Simpan file
            file.save(file_path)

            # Insert bukti_bukutamu
            insert_bukti_sql = """
                INSERT INTO bukti_bukutamu (id_bukutamu, foto_bukti, tanggal_cetak)
                VALUES (%s, %s, %s)
            """
            cursor.execute(insert_bukti_sql, (
                id_bukutamu,
                new_filename,
                data['tanggal_daftar']
            ))

        connection.commit()

        return jsonify({
            'statusCode': 200,
            'message': 'Pendaftaran dan bukti berhasil disimpan.'
        })

    except Exception as e:
        connection.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({
            'statusCode': 500,
            'message': 'Terjadi kesalahan. Semua perubahan dibatalkan.',
            'error': str(e)
        })


# ==== Flask Route ====
@app.route('/takePictureProcess', methods=['POST'])
def take_picture_handler():
    return process_image_route()

@app.route('/streamProcess', methods=['POST'])
def take_stream_handler():
    return stream_process()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002)
