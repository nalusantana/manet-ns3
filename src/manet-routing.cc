/*
 * manet-routing.cc
 *
 * Simulação MANET 802.11 ad hoc com AODV, OLSR ou DSDV, parametrizável por
 * linha de comando. Exporta uma linha por fluxo de dados medido pelo
 * FlowMonitor.
 */

#include "ns3/aodv-module.h"
#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/dsdv-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/internet-module.h"
#include "ns3/mobility-module.h"
#include "ns3/network-module.h"
#include "ns3/olsr-module.h"
#include "ns3/wifi-module.h"
#include "ns3/yans-wifi-helper.h"

#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("ManetRoutingExperiment");

namespace
{

/**
 * Indica se o arquivo já existe, para escrever o cabeçalho do CSV uma única vez.
 */
bool
FileExists(const std::string& path)
{
    std::ifstream f(path);
    return f.good();
}

/**
 * Nome do protocolo de roteamento instalado no nó (autoverificação).
 */
std::string
InstalledRoutingProtocol(Ptr<Node> node)
{
    Ptr<Ipv4> ipv4 = node->GetObject<Ipv4>();
    if (!ipv4 || !ipv4->GetRoutingProtocol())
    {
        return "NENHUM";
    }
    return ipv4->GetRoutingProtocol()->GetInstanceTypeId().GetName();
}

} // namespace

int
main(int argc, char* argv[])
{
    // -----------------------------------------------------------------------
    // 1. Parâmetros experimentais (todos por linha de comando)
    // -----------------------------------------------------------------------
    std::string protocol = "AODV";   // AODV | OLSR | DSDV
    std::string outCsv = "manet-results.csv";
    double speed = 10.0;             // m/s (velocidade constante por nó)
    double pause = 0.0;              // s   (pause time do Random Waypoint)
    double area = 500.0;             // m   (área quadrada: area x area)
    double simTime = 120.0;          // s   (tempo total de simulação)
    double appStart = 10.0;          // s   (início do tráfego UDP)
    double txPower = 7.5;            // dBm
    std::string rate = "256kbps";    // taxa oferecida por fluxo
    uint32_t nNodes = 20;            // quantidade de nós
    uint32_t nFlows = 4;             // fluxos simultâneos
    uint32_t packetSize = 1024;      // bytes
    uint32_t run = 1;                // número da execução (repetição)
    uint32_t seed = 12345;           // seed mestre
    bool verbose = false;            // imprime configuração detalhada

    CommandLine cmd(__FILE__);
    cmd.AddValue("protocol", "Protocolo de roteamento: AODV, OLSR ou DSDV", protocol);
    cmd.AddValue("speed", "Velocidade dos nós em m/s", speed);
    cmd.AddValue("pause", "Pause time do Random Waypoint em s", pause);
    cmd.AddValue("area", "Lado da área quadrada em m", area);
    cmd.AddValue("nodes", "Quantidade de nós", nNodes);
    cmd.AddValue("flows", "Número de fluxos UDP simultâneos", nFlows);
    cmd.AddValue("packetSize", "Tamanho do pacote UDP em bytes", packetSize);
    cmd.AddValue("rate", "Taxa oferecida por fluxo (ex.: 256kbps)", rate);
    cmd.AddValue("simTime", "Tempo total de simulação em s", simTime);
    cmd.AddValue("appStart", "Instante de início do tráfego UDP em s", appStart);
    cmd.AddValue("txPower", "Potência de transmissão em dBm", txPower);
    cmd.AddValue("run", "Número da execução / repetição (run do ns-3)", run);
    cmd.AddValue("seed", "Seed mestre do gerador aleatório", seed);
    cmd.AddValue("outCsv", "Arquivo CSV de saída (append)", outCsv);
    cmd.AddValue("verbose", "Imprime a configuração detalhada", verbose);
    cmd.Parse(argc, argv);

    // Normaliza o nome do protocolo para maiúsculas.
    for (auto& c : protocol)
    {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    if (protocol != "AODV" && protocol != "OLSR" && protocol != "DSDV")
    {
        NS_FATAL_ERROR("Protocolo invalido: " << protocol << " (use AODV, OLSR ou DSDV)");
    }
    if (nFlows > nNodes / 2)
    {
        NS_FATAL_ERROR("Numero de fluxos (" << nFlows << ") excede metade dos nos (" << nNodes
                                            << "): origem e destino precisam ser distintos.");
    }

    // -----------------------------------------------------------------------
    // 2. Reprodutibilidade: seed mestre fixa + run variável
    // -----------------------------------------------------------------------
    RngSeedManager::SetSeed(seed);
    RngSeedManager::SetRun(run);

    std::cout << "[CONFIG] protocol=" << protocol << " speed=" << speed << " pause=" << pause
              << " nodes=" << nNodes << " flows=" << nFlows << " packetSize=" << packetSize
              << " rate=" << rate << " simTime=" << simTime << " appStart=" << appStart
              << " area=" << area << "x" << area << " txPower=" << txPower << " seed=" << seed
              << " run=" << run << std::endl;

    // -----------------------------------------------------------------------
    // 3. Nós
    // -----------------------------------------------------------------------
    NodeContainer nodes;
    nodes.Create(nNodes);

    // -----------------------------------------------------------------------
    // 4. Wi-Fi IEEE 802.11 em modo Ad Hoc (sem infraestrutura)
    // -----------------------------------------------------------------------
    WifiHelper wifi;
    wifi.SetStandard(WIFI_STANDARD_80211b);

    YansWifiChannelHelper wifiChannel;
    wifiChannel.SetPropagationDelay("ns3::ConstantSpeedPropagationDelayModel");
    wifiChannel.AddPropagationLoss("ns3::FriisPropagationLossModel");

    YansWifiPhyHelper wifiPhy;
    wifiPhy.SetChannel(wifiChannel.Create());
    wifiPhy.Set("TxPowerStart", DoubleValue(txPower));
    wifiPhy.Set("TxPowerEnd", DoubleValue(txPower));

    // Taxa fixa (sem controle de taxa); broadcast usa a taxa básica.
    wifi.SetRemoteStationManager("ns3::ConstantRateWifiManager",
                                 "DataMode",
                                 StringValue("DsssRate11Mbps"),
                                 "ControlMode",
                                 StringValue("DsssRate1Mbps"));
    Config::SetDefault("ns3::WifiRemoteStationManager::NonUnicastMode",
                       StringValue("DsssRate1Mbps"));

    WifiMacHelper wifiMac;
    wifiMac.SetType("ns3::AdhocWifiMac");

    NetDeviceContainer devices = wifi.Install(wifiPhy, wifiMac, nodes);

    // -----------------------------------------------------------------------
    // 5. Mobilidade: Random Waypoint em área quadrada
    // -----------------------------------------------------------------------
    MobilityHelper mobility;

    // Criado explicitamente: sem isso o ns-3 usa o retângulo default (0..1 m).
    ObjectFactory pos;
    pos.SetTypeId("ns3::RandomRectanglePositionAllocator");
    {
        std::ostringstream x;
        std::ostringstream y;
        x << "ns3::UniformRandomVariable[Min=0.0|Max=" << area << "]";
        y << "ns3::UniformRandomVariable[Min=0.0|Max=" << area << "]";
        pos.Set("X", StringValue(x.str()));
        pos.Set("Y", StringValue(y.str()));
    }
    Ptr<PositionAllocator> positionAlloc = pos.Create()->GetObject<PositionAllocator>();

    std::ostringstream ssSpeed;
    std::ostringstream ssPause;
    ssSpeed << "ns3::UniformRandomVariable[Min=" << speed << "|Max=" << speed << "]";
    ssPause << "ns3::ConstantRandomVariable[Constant=" << pause << "]";

    mobility.SetMobilityModel("ns3::RandomWaypointMobilityModel",
                             "Speed",
                             StringValue(ssSpeed.str()),
                             "Pause",
                             StringValue(ssPause.str()),
                             "PositionAllocator",
                             PointerValue(positionAlloc));
    mobility.SetPositionAllocator(positionAlloc);
    mobility.Install(nodes);

    // -----------------------------------------------------------------------
    // 6. Pilha IP + protocolo de roteamento
    // -----------------------------------------------------------------------
    // Os helpers precisam permanecer vivos até internet.Install(nodes).
    AodvHelper aodv;
    OlsrHelper olsr;
    DsdvHelper dsdv;

    InternetStackHelper internet;
    if (protocol == "AODV")
    {
        internet.SetRoutingHelper(aodv);
    }
    else if (protocol == "OLSR")
    {
        internet.SetRoutingHelper(olsr);
    }
    else
    {
        internet.SetRoutingHelper(dsdv);
    }
    internet.Install(nodes);

    Ipv4AddressHelper ipv4;
    ipv4.SetBase("10.0.0.0", "255.0.0.0");
    Ipv4InterfaceContainer interfaces = ipv4.Assign(devices);

    // Autoverificação: confirma qual protocolo foi realmente instalado.
    std::cout << "[ROUTING] instalado=" << InstalledRoutingProtocol(nodes.Get(0)) << " nos=" << nNodes
              << std::endl;
    if (InstalledRoutingProtocol(nodes.Get(0)) == "NENHUM")
    {
        NS_FATAL_ERROR("Nenhum protocolo de roteamento instalado: o experimento seria invalido.");
    }

    // -----------------------------------------------------------------------
    // 7. Tráfego: nFlows fluxos UDP CBR (OnOff com OnTime=1, OffTime=0)
    // -----------------------------------------------------------------------
    const uint16_t dataPortBase = 9000;

    for (uint32_t i = 0; i < nFlows; ++i)
    {
        uint32_t src = i;
        uint32_t dst = nNodes - 1 - i; // pareamento espalhado pela topologia
        uint16_t port = static_cast<uint16_t>(dataPortBase + i);

        PacketSinkHelper sink("ns3::UdpSocketFactory",
                              InetSocketAddress(Ipv4Address::GetAny(), port));
        ApplicationContainer sinkApps = sink.Install(nodes.Get(dst));
        sinkApps.Start(Seconds(appStart));
        sinkApps.Stop(Seconds(simTime));

        OnOffHelper onoff("ns3::UdpSocketFactory",
                          InetSocketAddress(interfaces.GetAddress(dst), port));
        onoff.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
        onoff.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
        onoff.SetConstantRate(DataRate(rate), packetSize);
        ApplicationContainer srcApps = onoff.Install(nodes.Get(src));
        srcApps.Start(Seconds(appStart));
        srcApps.Stop(Seconds(simTime));

        if (verbose)
        {
            std::cout << "[FLOW " << i << "] " << interfaces.GetAddress(src) << " -> "
                      << interfaces.GetAddress(dst) << " porta " << port << std::endl;
        }
    }

    // -----------------------------------------------------------------------
    // 8. FlowMonitor
    // -----------------------------------------------------------------------
    FlowMonitorHelper flowmon;
    Ptr<FlowMonitor> monitor = flowmon.InstallAll();
    Ptr<Ipv4FlowClassifier> classifier =
        DynamicCast<Ipv4FlowClassifier>(flowmon.GetClassifier());

    // -----------------------------------------------------------------------
    // 9. Execução
    // -----------------------------------------------------------------------
    Simulator::Stop(Seconds(simTime));
    Simulator::Run();

    monitor->CheckForLostPackets();
    FlowMonitor::FlowStatsContainer stats = monitor->GetFlowStats();

    // -----------------------------------------------------------------------
    // 10. Exportação para CSV (uma linha por fluxo de dados)
    // -----------------------------------------------------------------------
    const double usefulTime = simTime - appStart; // janela útil de tráfego

    // Pacotes oferecidos por fluxo na janela útil, calculados pela taxa.
    const double rateBps = DataRate(rate).GetBitRate();
    const uint64_t offeredPerFlow =
        static_cast<uint64_t>(rateBps * usefulTime / (static_cast<double>(packetSize) * 8.0));

    bool needHeader = !FileExists(outCsv);
    std::ofstream out(outCsv, std::ios::app);
    if (!out.is_open())
    {
        NS_FATAL_ERROR("Nao foi possivel abrir o arquivo de saida: " << outCsv);
    }

    if (needHeader)
    {
        out << "protocol,speed,nodes,run,seed,flowId,srcAddr,dstAddr,dstPort,rate,packetSize,"
               "simTime,appStart,txPackets,rxPackets,lostPackets,offeredPackets,rxBytes,"
               "throughputMbps,pdrPct,deliveryRatioPct,delayMs,jitterMs"
            << "\n";
    }

    out << std::fixed << std::setprecision(4);

    uint64_t totalTx = 0;
    uint64_t totalRx = 0;
    uint32_t exportedFlows = 0;

    for (const auto& [flowId, st] : stats)
    {
        Ipv4FlowClassifier::FiveTuple tuple = classifier->FindFlow(flowId);

        // Ignora o tráfego de controle; só as portas de dados entram na medição.
        if (tuple.destinationPort < dataPortBase ||
            tuple.destinationPort >= dataPortBase + nFlows)
        {
            continue;
        }

        const double throughputMbps =
            (usefulTime > 0.0) ? (st.rxBytes * 8.0 / usefulTime / 1e6) : 0.0;
        const double pdrPct =
            (st.txPackets > 0) ? (100.0 * st.rxPackets / static_cast<double>(st.txPackets)) : 0.0;
        const double delayMs =
            (st.rxPackets > 0)
                ? (st.delaySum.GetSeconds() / static_cast<double>(st.rxPackets) * 1000.0)
                : 0.0;
        const double jitterMs =
            (st.rxPackets > 1)
                ? (st.jitterSum.GetSeconds() / static_cast<double>(st.rxPackets - 1) * 1000.0)
                : 0.0;
        const double deliveryRatioPct =
            (offeredPerFlow > 0)
                ? (100.0 * st.rxPackets / static_cast<double>(offeredPerFlow))
                : 0.0;

        out << protocol << ',' << speed << ',' << nNodes << ',' << run << ',' << seed << ','
            << flowId << ',' << tuple.sourceAddress << ',' << tuple.destinationAddress << ','
            << tuple.destinationPort << ',' << rate << ',' << packetSize << ',' << simTime << ','
            << appStart << ',' << st.txPackets << ',' << st.rxPackets << ',' << st.lostPackets << ','
            << offeredPerFlow << ',' << st.rxBytes << ',' << throughputMbps << ',' << pdrPct << ','
            << deliveryRatioPct << ',' << delayMs << ',' << jitterMs << "\n";

        totalTx += st.txPackets;
        totalRx += st.rxPackets;
        ++exportedFlows;
    }
    out.close();

    const double aggregatePdr =
        (totalTx > 0) ? (100.0 * totalRx / static_cast<double>(totalTx)) : 0.0;

    // Resumo em stdout: permite conferir uma execução sem abrir o CSV.
    std::cout << "[RESULT] protocol=" << protocol << " speed=" << speed << " run=" << run
              << " nodes=" << nNodes << " flowsExportados=" << exportedFlows
              << " tx=" << totalTx << " rx=" << totalRx << " pdrAgregado=" << std::fixed
              << std::setprecision(2) << aggregatePdr << "%" << std::endl;
    std::cout << "[OUTPUT] " << outCsv << std::endl;

    Simulator::Destroy();
    return 0;
}
