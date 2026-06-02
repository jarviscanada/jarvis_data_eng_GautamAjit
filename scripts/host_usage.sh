# Setup and validate arguments
psql_host=$1
psql_port=$2
db_name=$3
psql_user=$4
psql_password=$5

# Check number of args
if [ "$#" -ne 5 ]; then
	echo "Illegal number of parameters"
	exit 1
fi

# Save machine statistics in MB and current machine hostname to variables
vmstat_mb=$(vmstat --unit M)
vmstat_mbd=$(vmstat --unit M -d)
disk_data=$(df -BM /)
hostname=$(hostname -f)

# Retrieve hardware specification variables
# xargs is a trick to trim leading and trailing white spaces
timestamp=$(date "+%Y-%m-%d %H:%M:%S")
export PGPASSWORD=$psql_password
host_id=$(psql -t -A -h $psql_host -p $psql_port -d $db_name -U $psql_user -c "SELECT id FROM host_info WHERE hostname='$hostname';" | xargs)
memory_free=$(echo "$vmstat_mb" | awk '{print $4}'| tail -n1 | xargs)
cpu_idle=$(echo "$vmstat_mb" | tail -1 | awk -v col="15" '{print $col}')
cpu_kernel=$(echo "$vmstat_mb" | tail -1 | awk -v col="14" '{print $col}')
disk_io=$(echo "$vmstat_mbd" | tail -1 | awk -v col="10" '{print $col}')
disk_available=$(echo "$disk_data" | tail -1 | awk -v col="4" '{print substr($col, 1, length($col)-1)}')

insert_stmt="INSERT INTO host_usage(timestamp, host_id, memory_free, cpu_idle, cpu_kernel, disk_io, disk_available) VALUES('$timestamp', '$host_id', '$memory_free', '$cpu_idle', '$cpu_kernel', '$disk_io', '$disk_available')"

#Insert data into a database
psql -h $psql_host -p $psql_port -d $db_name -U $psql_user -c "$insert_stmt"
exit $?
