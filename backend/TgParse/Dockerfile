# syntax=docker/dockerfile:1.4
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
WORKDIR /app

#RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY *.csproj ./

RUN --mount=type=cache,id=nuget,target=/root/.nuget/packages \
    dotnet restore

COPY . .
RUN --mount=type=cache,id=nuget,target=/root/.nuget/packages \
    dotnet publish -c Release -o /app/out

FROM mcr.microsoft.com/dotnet/aspnet:9.0
WORKDIR /app
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
COPY --from=build /app/out ./

EXPOSE 8002

ENV ASPNETCORE_URLS=http://+:8002
ENV ASPNETCORE_ENVIRONMENT=Production
ENTRYPOINT ["dotnet", "TgParse.dll"]
