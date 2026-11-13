## Set up the local database

From the root directory, run these commands to create the database tables and
populate them with sample data:

```
python3 schema.py
python3 sample_data.py
```

Can confirm the seed was successful by running:

```
sqlite3 therapy_link.db
```

Check for records in tables:

```
SELECT * FROM users;
SELECT * FROM appointments;
```

Brief: 
[https://ucl-eu-west-2-moodle-sitedata.s3.eu-west-2.amazonaws.com/44/63/44636c40c939d6c8b3955a68a07d47ebcc1d92e8?response-content-disposition=inline%3B%20filename%3D%22COMP0066_Coursework-2026-27_TherapyLink.pdf%22&response-content-type=application%2Fpdf&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIA47YHZF637GKGWUJC%2F20261110%2Feu-west-2%2Fs3%2Faws4_request&X-Amz-Date=20261110T152137Z&X-Amz-SignedHeaders=host&X-Amz-Expires=21563&X-Amz-Signature=1bbbcf1fd838886fa80e53bf65a2468a35e318c0cce8bf252ea6c95c324e2ec2#objectfs-origin=/pluginfile.php/10219204/mod_resource/content/5/COMP0066_Coursework-2026-27_TherapyLink.pdf](https://ucl-eu-west-2-moodle-sitedata.s3.eu-west-2.amazonaws.com/b5/ad/b5adab0f03b118fba33bfdb2b06f8ba303abdfe4?response-content-disposition=inline%3B%20filename%3D%22COMP0066_Coursework-2026-27_TherapyLink.pdf%22&response-content-type=application%2Fpdf&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIA47YHZF637GKGWUJC%2F20261113%2Feu-west-2%2Fs3%2Faws4_request&X-Amz-Date=20261113T091423Z&X-Amz-SignedHeaders=host&X-Amz-Expires=21577&X-Amz-Signature=998a21cd3b601a4fc9167e013910fc98200e5283a57580b4b154a6c48481039e#objectfs-origin=/pluginfile.php/10219204/mod_resource/content/6/COMP0066_Coursework-2026-27_TherapyLink.pdf)
