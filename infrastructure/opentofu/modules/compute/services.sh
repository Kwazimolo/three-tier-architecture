#!/bin/bash

# Log output for debugging
exec > /var/log/user-data.log 2>&1
set -x

# Update packages
sudo yum update -y

# Install necessary packages
sudo amazon-linux-extras enable php7.2
sudo yum install -y httpd mariadb-server php-mbstring php-xml

# Start and enable Apache
sudo systemctl start httpd
sudo systemctl enable httpd

# Set permissions for Apache
sudo usermod -a -G apache ec2-user
sudo chown -R ec2-user:apache /var/www
sudo chmod 2775 /var/www && find /var/www -type d -exec sudo chmod 2775 {} \;
find /var/www -type f -exec sudo chmod 0664 {} \;

# Create the index.html file
echo '<h1>Hello world from a highly available group of EC2 instances</h1>' | sudo tee /var/www/html/index.html

# Restart Apache to apply changes
sudo systemctl restart httpd