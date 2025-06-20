FROM python:3.13.1

RUN apt-get update && apt-get install -y \
    gcc g++ make libffi-dev libssl-dev \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --upgrade pip setuptools wheel

COPY requirements.txt .

RUN pip install --no-cache-dir \
    --find-links https://download.pytorch.org/whl/torch_stable.html \
    --prefer-binary \
    --retries 5 \
    --timeout 120 \
    -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
