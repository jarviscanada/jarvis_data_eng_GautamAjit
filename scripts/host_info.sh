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
hostname=$(hostname -f)

lscpu_out=`lscpu`
# hardware info
hostname=$(hostname -f)
cpu_number=$(echo "$lscpu_out"  | egrep "^CPU\(s\):" | awk '{print $2}' | xargs)
cpu_architecture=$(echo "$lscpu_out"  | egrep "Model name:" | awk '{print substr($0, index($0,$3))}' | xargs)
cpu_model=$(echo "$lscpu_out"  | egrep "Model:" | awk '{print $2}' | xargs)
cpu_mhz=$(cat /proc/cpuinfo | egrep "cpu MHz" | awk '{print $4}' | sort -u |xargs) 
l2_cache=$(echo "$lscpu_out"  | egrep "L2 cache:" | awk '{print $3}' | xargs)
total_mem=$(echo "$vmstat_mb" | tail -1 | awk '{print $4}')
timestamp=$(date "+%Y-%m-%d %H:%M:%S")

insert_stmt="INSERT INTO host_info(hostname, cpu_number, cpu_architecture, cpu_model, cpu_mhz, l2_cache, timestamp, total_mem) VALUES('$hostname', '$cpu_number', '$cpu_architecture', '$cpu_model', '$cpu_mhz', '$l2_cache', '$timestamp', '$total_mem')"

#set up env var for psql cmd
export PGPASSWORD=$psql_password
#Insert data into a database
psql -h $psql_host -p $psql_port -d $db_name -U $psql_user -c "$insert_stmt"
exit $?
