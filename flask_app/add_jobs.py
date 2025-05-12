from app import app, db, Job

with app.app_context():
    # Create tables if they don't exist
    db.create_all()
    
    # Delete existing jobs first (optional - remove this if you want to keep existing jobs)
    Job.query.delete()
    db.session.commit()
      # Create sample jobs
    jobs = [
        Job(
            title='Full Stack Developer',
            company='Microsoft',
            description='Seeking a Full Stack Developer with 3+ years of experience in Python/Django and React. Must have strong understanding of web technologies and database design.',
            location='Bangalore, India',
            employer_id=2
        ),
        Job(
            title='AI Research Scientist',
            company='OpenAI',
            description='Looking for an AI Research Scientist with expertise in deep learning and natural language processing. PhD in Computer Science or related field required.',
            location='Mumbai, India',
            employer_id=2
        ),
        Job(
            title='Cloud Solutions Architect',
            company='Amazon Web Services',
            description='Seeking an experienced Cloud Solutions Architect to design and implement scalable cloud infrastructure. AWS certification required.',
            location='Hyderabad, India',
            employer_id=2
        ),
        Job(
            title='Cybersecurity Analyst',
            company='IBM',
            description='Looking for a Cybersecurity Analyst with expertise in threat detection and incident response. CISSP certification preferred.',
            location='Pune, India',
            employer_id=2
        ),
        Job(
            title='Blockchain Developer',
            company='Ethereum Foundation',
            description='Seeking a Blockchain Developer with experience in smart contract development and DApp creation. Solidity expertise required.',
            location='Bangalore, India',
            employer_id=2
        ),
        Job(
            title='Product Manager',
            company='Flipkart',
            description='Looking for an experienced Product Manager to lead product development initiatives. Strong analytical and leadership skills required.',
            location='Delhi, India',
            employer_id=2
        ),
        Job(
            title='Data Engineer',
            company='Oracle',
            description='Seeking a Data Engineer with expertise in building data pipelines and ETL processes. Experience with big data technologies required.',
            location='Chennai, India',
            employer_id=2
        ),
        Job(
            title='Mobile Game Developer',
            company='Ubisoft',
            description='Looking for a Mobile Game Developer with Unity/Unreal Engine experience. Strong understanding of game mechanics and optimization required.',
            location='Pune, India',
            employer_id=2
        ),
        Job(
            title='Technical Project Manager',
            company='Infosys',
            description='Seeking a Technical Project Manager with Agile/Scrum experience. PMP certification and strong leadership skills required.',
            location='Bangalore, India',
            employer_id=2
        ),
        Job(
            title='UI/UX Researcher',
            company='Adobe',
            description='Looking for a UI/UX Researcher to conduct user research and usability testing. Experience with design thinking and user-centered design required.',
            location='Hyderabad, India',
            employer_id=2
        ),
        Job(
            title='Data Scientist',
            company='Google',
            description='Looking for an experienced Data Scientist with strong background in machine learning, statistical analysis, and big data technologies. PhD in related field preferred.',
            location='Hyderabad, India',
            employer_id=2
        ),
        Job(
            title='UX Designer',
            company='Amazon',
            description='Creative UX Designer needed with 3+ years experience in user interface design, wireframing, and prototyping. Experience with Figma and Adobe Creative Suite required.',
            location='Mumbai, India',
            employer_id=2
        ),
        Job(
            title='DevOps Engineer',
            company='Netflix',
            description='DevOps Engineer with expertise in AWS, Docker, Kubernetes, and CI/CD pipelines. Must have experience with microservices architecture.',
            location='Delhi, India',
            employer_id=2
        ),
        Job(
            title='Mobile App Developer',
            company='Apple',
            description='iOS Developer with strong knowledge of Swift and UIKit. Experience with SwiftUI and Core Data is a plus.',
            location='Pune, India',
            employer_id=2
        )
    ]

    # Add all jobs to the database
    for job in jobs:
        db.session.add(job)

    # Commit the changes
    db.session.commit()

    print("Jobs added successfully!")

    # Print all jobs to verify
    all_jobs = Job.query.all()
    for job in all_jobs:
        print(f"ID: {job.id}, Title: {job.title}, Company: {job.company}, Location: {job.location}")
