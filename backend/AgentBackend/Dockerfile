# Этап сборки
FROM mcr.microsoft.com/dotnet/aspnet:9.0  AS base
WORKDIR /app
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
WORKDIR /src
COPY ["AgentBackend/AgentBackend.csproj", "."]
RUN dotnet restore "AgentBackend.csproj"
COPY . .
WORKDIR /src/AgentBackend
RUN dotnet build "AgentBackend.csproj" -c Release -o /app


# Этап выполнения
FROM base AS runtime
WORKDIR /app
COPY --from=build /app/ .


ENTRYPOINT ["dotnet", "AgentBackend.dll"]