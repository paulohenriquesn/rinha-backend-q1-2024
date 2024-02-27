FROM nikolaik/python-nodejs:latest	

WORKDIR /usr/src/app

COPY . ./

RUN npm install

RUN pip install -r requirements.txt

CMD ["npm", "run", "dev"]