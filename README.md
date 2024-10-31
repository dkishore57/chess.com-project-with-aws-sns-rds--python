This Python application fetches Chess.com games for a user based on a minimum accuracy requirement and sends game links via email using AWS SNS and stores the username and email in aws rds database.

Features
Fetch Chess.com games for a specified user and year.
Filter games by minimum accuracy.
Send filtered game links to an email using AWS SNS.
Requirements
Python 3.x
AWS credentials with SNS access and RDS.

Dependencies: requests, boto3, mysql-connector-python