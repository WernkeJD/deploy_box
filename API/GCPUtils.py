import python_terraform

def deploy_gcp(mongodb_uri: str,frontend_image: str, backend_image: str):
    var = {
        "MONGO_URI": mongodb_uri,
        "FRONTEND_IMAGE": frontend_image,
        "BACKEND_IMAGE": backend_image
    }


    tf = python_terraform.Terraform(working_dir=".")
    print(tf.init())
    print(tf.plan(var=var))
    print(tf.apply(var=var, skip_plan=True))


if __name__ == '__main__':
    deploy_gcp("mongodb://localhost:27017", "us-central1-docker.pkg.dev/PROJECT_ID/mern-frontend", "us-central1-docker.pkg.dev/PROJECT_ID/mern-backend")