import python_terraform



def deploy_gcp(mongodb_uri: str):
    var = {
        "MONGO_URI": mongodb_uri,
    }


    tf = python_terraform.Terraform(working_dir=".")
    print(tf.init())
    print(tf.plan(vars=var))
    print(tf.apply(vars=var, skip_plan=True))

if __name__ == "__main__":
    print(deploy_gcp("mongodb+srv://admin:Dramatic23!@cluster0.ykomc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"))