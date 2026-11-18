SELECT u.name AS user_name, c.name AS condition_name
FROM patient_conditions as pc
JOIN users as u on pc.patient_id = u.user_id
JOIN conditions as c on pc.condition_id = c.condition_id;
