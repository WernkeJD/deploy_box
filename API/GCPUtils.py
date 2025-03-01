import python_terraform

def deploy_gcp(mongodb_uri: str):
    var = {
        "MONGO_URI": mongodb_uri,
    }


    tf = python_terraform.Terraform(working_dir=".")
    print(tf.init())
    print(tf.plan(vars=var))
    print(tf.apply(vars=var, skip_plan=True))
